#!/usr/bin/env python

import os
import boto3
import time
import datetime
import json
import re
import subprocess


def timestamp():
    """ Return simple timestamp """
    return '{:%H:%M:%S}'.format(datetime.datetime.now())


def create_stream(sname):
    """ Create kinesis stream, and wait until it is active """
    kinesis = boto3.client('kinesis')
    if sname not in [f for f in kinesis.list_streams()['StreamNames']]:
        print '%s: Creating Kinesis stream %s' % (timestamp(), sname)
        kinesis.create_stream(StreamName=sname, ShardCount=1)
    else:
        print '%s: Kinesis stream %s exists' % (timestamp(), sname)
    while kinesis.describe_stream(StreamName=sname)['StreamDescription']['StreamStatus'] == 'CREATING':
        time.sleep(2)
    return kinesis.describe_stream(StreamName=sname)['StreamDescription']


def create_role(name):
    """ Create a role with an inline policy for accessing kinesis streams """
    rolename = '%s_lambda_kinesis' % name
    iam = boto3.client('iam')
    policydoc = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": ["lambda.amazonaws.com"]}, "Action": ["sts:AssumeRole"]},
        ]
    }
    roles = [r['RoleName'] for r in iam.list_roles()['Roles']]
    if rolename in roles:
        print '%s: IAM role %s exists' % (timestamp(), rolename)
        role = iam.get_role(RoleName=rolename)['Role']
    else:
        print '%s: Creating IAM role %s' % (timestamp(), rolename)
        role = iam.create_role(RoleName=rolename, AssumeRolePolicyDocument=json.dumps(policydoc))['Role']

    # attach inline policy
    parn = 'arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole'
    iam.attach_role_policy(RoleName=rolename, PolicyArn=parn)
    return role


def create_function(name, zfile, lsize=512, timeout=10, update=False):
    """ Create, or update if exists, lambda function """
    # create role for this function
    role = create_role(name)
    l = boto3.client('lambda')
    with open(zfile, 'rb') as zipfile:
        funcs = l.list_functions()['Functions']
        if name in [f['FunctionName'] for f in funcs]:
            if update:
                print '%s: Updating %s lambda function code' % (timestamp(), name)
                return l.update_function_code(FunctionName=name, ZipFile=zipfile.read())
            else:
                print '%s: Lambda function %s exists' % (timestamp(), name)
                for f in funcs:
                    if f['FunctionName'] == name:
                        return f
        else:
            print '%s: Creating %s lambda function' % (timestamp(), name)
            return l.create_function(
                FunctionName=name,
                Runtime='nodejs',
                Role=role['Arn'],
                Handler='examples/kinesis-consumer/index.handler',
                Description='OSM Stats Worker',
                Timeout=timeout,
                MemorySize=lsize,
                Publish=True,
                Code={'ZipFile': zipfile.read()}
            )


def create_database(name, password, dbclass='db.t2.medium', storage=5):
    """ Create an RDS database and seed it """
    rds = boto3.client('rds')
    dbname = re.sub('[^0-9a-zA-Z]+', '', name)

    # TODO - check if DB exists
    dbs = [db['DBInstanceIdentifier'] for db in rds.describe_db_instances()['DBInstances']]
    if name not in dbs:
        print '%s: Creating RDS database %s' % (timestamp(), name)
        db = rds.create_db_instance(
            DBName=dbname, DBInstanceIdentifier=name, DBInstanceClass=dbclass, Engine='postgres',
            MasterUsername=dbname, MasterUserPassword=password, VpcSecurityGroupIds=['sg-5e742627'],
            AllocatedStorage=storage
        )['DBInstance']
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=name)
    else:
        print '%s: RDS Database %s exists' % (timestamp(), name)
    db = rds.describe_db_instances(DBInstanceIdentifier=name)['DBInstances'][0]
    dburl = 'postgres://%s:%s@%s:%s/%s' % \
            (dbname, password, db['Endpoint']['Address'], db['Endpoint']['Port'], dbname)
    os.environ['DATABASE_URL'] = dburl
    db['URL'] = dburl
    return db


def create_ec2(name, instancetype='t2.medium', AMI='ami-60b6c60a'):
    """ Create an EC2 instance of provided type and AMI """
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    # TODO - add security group
    try:
        instances = ec2.describe_instances(Filters=[
            {'Name': 'tag:Name', 'Values': [name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
        ])
        print '%s: EC2 instance %s exists' % (timestamp(), name)
        iid = instances['Reservations'][0]['Instances'][0]['InstanceId']
    except Exception:
        # the instance did not exist
        keyname = name+'_keypair'
        # delete and previous key by this name and issue a new one
        try:
            ec2.delete_key_pair(KeyName=keyname)
        except Exception:
            pass
        # create a keypair
        key_pair = ec2.create_key_pair(KeyName=keyname)
        pfile = name + '.pem'
        with open(pfile, 'w') as f:
            f.write(key_pair['KeyMaterial'])
        os.chmod(pfile, 0600)

        print '%s: Creating EC2 instance %s' % (timestamp(), name)
        instances = ec2resource.create_instances(
            ImageId=AMI, MinCount=1, MaxCount=1, KeyName=keyname, SecurityGroups=['launch-wizard-5'],
            InstanceType=instancetype, Monitoring={'Enabled': True}
        )
        iid = instances[0].instance_id
        # set name
        ec2.create_tags(Resources=[iid], Tags=[{'Key': 'Name', 'Value': name}])
    inst = ec2resource.Instance(iid)
    inst.wait_until_running()
    return inst