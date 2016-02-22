#!/usr/bin/env python

import os
import boto3
import time
import datetime
import json
import re
from urllib2 import urlopen



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


def get_or_create_role(name, policies=None, instance_profile=False):
    """ Create a role with an optional inline policy """
    iam = boto3.client('iam')
    policydoc = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": ["lambda.amazonaws.com"]}, "Action": ["sts:AssumeRole"]},
        ]
    }
    roles = [r['RoleName'] for r in iam.list_roles()['Roles']]
    if name in roles:
        print '%s: IAM role %s exists' % (timestamp(), name)
        role = iam.get_role(RoleName=name)['Role']
    else:
        print '%s: Creating IAM role %s' % (timestamp(), name)
        role = iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(policydoc))['Role']

    # attach inline policy
    if policies is not None:
        for p in policies:
            iam.attach_role_policy(RoleName=role['RoleName'], PolicyArn=p)
    # add role to an instance profile and return that
    if instance_profile:
        profiles = iam.list_instance_profiles()['InstanceProfiles']
        for p in profiles:
            if p['InstanceProfileName'] == name:
                return p
        profile = iam.create_instance_profile(InstanceProfileName=name)['InstanceProfile']
        iam.add_role_to_instance_profile(InstanceProfileName=profile['InstanceProfileName'],
                                         RoleName=role['RoleName'])
        # time.sleep(5)
        return profile
    else:
        return role


def create_function(name, zfile, lsize=512, timeout=10, update=False):
    """ Create, or update if exists, lambda function """
    # create role for this function
    role = get_or_create_role(name + '_lambda',
                              policies=['arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole',
                                        'arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole'])
    l = boto3.client('lambda')
    ec2 = boto3.client('ec2')
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
            group = get_or_create_security_group('%s_lambda' % name)
            # subnets = [s['SubnetId'] for s in ec2.describe_subnets()['Subnets']]
            return l.create_function(
                FunctionName=name,
                Runtime='nodejs',
                Role=role['Arn'],
                Handler='examples/kinesis-consumer/index.handler',
                Description='OSM Stats Worker',
                Timeout=timeout,
                MemorySize=lsize,
                Publish=True,
                Code={'ZipFile': zipfile.read()},
                # VpcConfig={'SubnetIds': subnets, 'SecurityGroupIds': [group.group_id]}
            )


def create_database(name, password, dbclass='db.t2.medium', storage=5):
    """ Create an RDS database and seed it """
    rds = boto3.client('rds')
    dbname = re.sub('[^0-9a-zA-Z]+', '', name)

    # TODO - check if DB exists
    dbs = [db['DBInstanceIdentifier'] for db in rds.describe_db_instances()['DBInstances']]
    if name not in dbs:
        my_ip = json.load(urlopen('https://api.ipify.org/?format=json'))['ip'] + '/32'
        my_ip = '0.0.0.0/0'
        perms = [
            {'IpProtocol': 'tcp', 'FromPort': 5432, 'ToPort': 5432, 'IpRanges': [{'CidrIp': my_ip}]},
        ]
        group = get_or_create_security_group('%s_rds' % name, permissions=perms)

        print '%s: Creating RDS database %s' % (timestamp(), name)

        db = rds.create_db_instance(
            DBName=dbname, DBInstanceIdentifier=name, DBInstanceClass=dbclass, Engine='postgres',
            MasterUsername=dbname, MasterUserPassword=password, VpcSecurityGroupIds=[group.group_id],
            # VpcSecurityGroupIds=['sg-5e742627'],
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


def create_security_group(name, permissions=None):
    """ Create security group or retrieve existing and allow SSH and HTTP """
    ec2 = boto3.client('ec2')
    ec2r = boto3.resource('ec2')
    try:
        gid = ec2.describe_security_groups(GroupNames=[name])['SecurityGroups'][0]['GroupId']
    except:
        # security group does not exist
        print '%s: Creating security group %s' % (timestamp(), name)
        gid = ec2.create_security_group(GroupName=name, Description=name)['GroupId']
    group = ec2r.SecurityGroup(gid)
    # add SSH and HTTP inbound rules
    if permissions is not None:
        ec2.authorize_security_group_ingress(
            GroupId=group.group_id,
            IpPermissions=permissions,
        )
    return group


def get_or_create_security_group(name, permissions=None):
    """ Get or create a security group of this name """
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    filts = [{'Name': 'group-name', 'Values': [name]}]
    groups = ec2.describe_security_groups(Filters=filts)['SecurityGroups']
    if len(groups) == 0:
        group = create_security_group(name, permissions=permissions)
    else:
        group = ec2resource.SecurityGroup(groups[0]['GroupId'])
    return group


def get_ec2(name):
    """ Retrieve matchine EC2 or return None """
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    try:
        instances = ec2.describe_instances(Filters=[
            {'Name': 'tag:Name', 'Values': [name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
        ])
        inst = ec2resource.Instance(instances['Reservations'][0]['Instances'][0]['InstanceId'])
        return inst
    except Exception:
        return None


def create_ec2(name, instancetype='t2.medium', AMI='ami-60b6c60a'):
    """ Create an EC2 instance of provided type and AMI """
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    try:
        instances = ec2.describe_instances(Filters=[
            {'Name': 'tag:Name', 'Values': [name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
        ])
        inst = ec2resource.Instance(instances['Reservations'][0]['Instances'][0]['InstanceId'])
        print '%s: EC2 instance %s exists' % (timestamp(), name)
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

        # create a security group with permissions
        perms = [
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ]
        group = get_or_create_security_group('%s_ec2' % name, permissions=perms)

        # create role
        role = get_or_create_role('%s_ec2' % name, instance_profile=True,
                           policies=['arn:aws:iam::aws:policy/CloudWatchFullAccess'])

        print '%s: Creating EC2 instance %s' % (timestamp(), name)
        instances = ec2resource.create_instances(
            ImageId=AMI, MinCount=1, MaxCount=1, KeyName=keyname, SecurityGroups=[group.group_name],
            InstanceType=instancetype, Monitoring={'Enabled': True},
            IamInstanceProfile={'Arn': role['Arn']}
        )
        iid = instances[0].instance_id
        # set name
        ec2.create_tags(Resources=[iid], Tags=[{'Key': 'Name', 'Value': name}])
        inst = ec2resource.Instance(iid)
        inst.wait_until_running()
        inst.reload()
        # give it additional time for SSH to fully start
        time.sleep(60)
    return inst
