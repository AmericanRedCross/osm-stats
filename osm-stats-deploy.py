#!/usr/bin/env python

import os
import sys
import argparse
import boto3
import time
import subprocess
import json
import datetime
import re
from fabric.api import settings
from fabfile import deploy

'''
Use 'aws configure' to configure credentials and default region
'''


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


def create_function(lname, zfile, rolearn, lsize=512, timeout=10, update=False):
    """ Create, or update if exists, lambda function """
    l = boto3.client('lambda')
    with open(zfile, 'rb') as zipfile:
        funcs = l.list_functions()['Functions']
        if lname in [f['FunctionName'] for f in funcs]:
            if update:
                print '%s: Updating %s lambda function code' % (timestamp(), lname)
                return l.update_function_code(FunctionName=lname, ZipFile=zipfile.read())
            else:
                print '%s: Lambda function %s exists' % (timestamp(), lname)
                for f in funcs:
                    if f['FunctionName'] == lname:
                        return f
        else:
            print '%s: Creating %s lambda function' % (timestamp(), lname)
            return l.create_function(
                FunctionName=lname,
                Runtime='nodejs',
                Role=rolearn,
                Handler='examples/kinesis-consumer/index.handler',
                Description='OSM Stats Worker',
                Timeout=timeout,
                MemorySize=lsize,
                Publish=True,
                Code={'ZipFile': zipfile.read()}
            )


def create_database(name, password, dbclass='db.t2.medium', storage=5, migrate=True):
    """ Create an RDS database and seed it """
    rds = boto3.client('rds')
    dbname = re.sub('[^0-9a-zA-Z]+', '', name)

    # TODO - check if DB already exists
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
        print '%s: RDS Database %s already exists' % (timestamp(), name)
    db = rds.describe_db_instances(DBInstanceIdentifier=name)['DBInstances'][0]
    dburl = 'postgres://%s:%s@%s:%s/%s' % \
            (dbname, args.password, db['Endpoint']['Address'], db['Endpoint']['Port'], dbname)
    os.environ['DATABASE_URL'] = dburl
    db['URL'] = dburl
    if migrate:
        FNULL = open(os.devnull, 'w')
        # db migration - this is ugly way of doing this
        os.chdir('osm-stats-workers/src/db/migrations')
        subprocess.call(['knex', 'migrate:latest'], stdout=FNULL)
        subprocess.call(['knex', 'seed:run'], stdout=FNULL)
        os.chdir('../../../../')
    return db


def create_ec2(name, instancetype='t2.medium'):
    """ Create an EC2 instance with an Ubuntu image """
    ec2 = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')
    # TODO - add security group
    # TODO - this doesn't properly check existing instance
    try:
        instances = ec2.describe_instances(InstanceIds=[name])
        iid = instances['Reservations'][0]['Instances'][0]['InstanceId']
    except Exception:
        # the instance did not exist
        keyname = name+'_keypair'
        # if it already exists, delete and issue a new one
        try:
            ec2.delete_key_pair(KeyName=keyname)
        except Exception, e:
            pass
        # create a keypair
        key_pair = ec2.create_key_pair(KeyName=keyname)
        pfile = name + '.pem'
        with open(pfile, 'w') as f:
            f.write(key_pair['KeyMaterial'])
        os.chmod(pfile, 0600)

        print '%s: Creating EC2 instance %s' % (timestamp(), name)
        instances = ec2resource.create_instances(
            ImageId='ami-60b6c60a', MinCount=1, MaxCount=1, KeyName=keyname, SecurityGroups=['launch-wizard-5'],
            InstanceType=instancetype, Monitoring={'Enabled': True}
        )
        instances[0].wait_until_running()
        iid = instances[0].instance_id
    return ec2resource.Instance(iid)


if __name__ == "__main__":
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser0 = argparse.ArgumentParser(description='Deploy OSM Stats', formatter_class=dhf)
    parser0.add_argument('--name', help='Base name for all AWS resources', default='osmstats')
    parser0.add_argument('--lsize', help='Size (MB) of Lambda function', default=512)
    parser0.add_argument('--ltimeout', help='Timeout (seconds) of Lambda function', default=10)
    parser0.add_argument('--update', help='Update with latest code', default=False)
    parser0.add_argument('--dbclass', help='The Amazon instance class for the RDS database', default='db.t2.medium')
    parser0.add_argument('--password', help='The password to use for database', default='t3sting9huy')

    args = parser0.parse_args()
    '{:%H:%M:%S}'.format(datetime.datetime.now())
    print '%s: Starting deployment of %s' % (timestamp(), args.name)

    # clone/ workers repo and create zip
    repo = 'osm-stats-workers'
    repo_url = 'https://github.com/AmericanRedCross/osm-stats-workers.git'
    FNULL = open(os.devnull, 'w')
    if not os.path.exists(repo):
        print '%s: Cloning %s repository' % (timestamp(), repo)
        subprocess.call(['git', 'clone', '-bgh-pages', repo_url], stdout=FNULL, stderr=FNULL)
    zfile = 'osm-stats-workers/osm-stats-workers.zip'
    # unzip migration files
    subprocess.call(['unzip', '-o', zfile, '-d', repo], stdout=FNULL)

    # create stream and RDS database
    stream = create_stream(args.name)
    db = create_database(args.name, args.password, dbclass=args.dbclass)

    # set up environment variables
    lname = args.name + '-worker'
    env = [
        'KINESIS_STREAM=%s' % args.name,
        'LAMBDA_FUNCTION=%s' % lname,
        'DATABASE_URL=%s' % db['URL']
    ]

    # create environment variable file
    with open('.env', 'w') as f:
        [f.write(e + '\n') for e in env]

    # add .env file to zip
    subprocess.call(['zip', '%s/%s.zip' % (repo, repo), '-xi', '.env'], stdout=FNULL)

    # create or update lambda function
    role = create_role(args.name)
    func = create_function(lname, zfile, role['Arn'], lsize=args.lsize, timeout=args.ltimeout, update=args.update)

    # create mapping to kinesis stream
    batchsz = 1     # for now, this must be one
    l = boto3.client('lambda')
    sources = l.list_event_source_mappings(FunctionName=lname,
                                           EventSourceArn=stream['StreamARN'])['EventSourceMappings']
    # add if this stream is not already mapped
    if stream['StreamARN'] not in [s['EventSourceArn'] for s in sources]:
        l.create_event_source_mapping(FunctionName=lname, EventSourceArn=stream['StreamARN'],
                                      BatchSize=batchsz, StartingPosition='TRIM_HORIZON')

    # start up EC2 instance
    ec2 = create_ec2(args.name)
    env.append('EC2_URL=%s' % ec2.public_dns_name)
    host_string = 'ec2-user@%s' % ec2.public_dns_name

    #with settings(host_string=host_string, key_filename=args.name + '.pem'):
    #    deploy()

    # docker compose up
    print '%s: Completed deployment of %s' % (timestamp(), args.name)
    [sys.stdout.write('\t%s\n' % e) for e in env]
