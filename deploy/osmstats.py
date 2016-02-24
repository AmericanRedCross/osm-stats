#!/usr/bin/env python

import os
import sys
import argparse
import boto3
import subprocess
import shutil
from boto3utils import timestamp, create_stream, create_function, create_database, create_ec2
from fabric.api import settings
import fabfile

'''
    OSM Stats AWS deployment script
'''


def clone_workers_repo(logfile=None):
    """ Clone workers repository """
    if logfile is None:
        logfile = open(os.devnull, 'w')
    repo = 'osm-stats-workers'
    print '%s: Fetching latest %s repository' % (timestamp(), repo)
    repo_url = 'https://github.com/AmericanRedCross/%s.git' % repo
    if os.path.exists(repo):
        shutil.rmtree(repo)
    subprocess.call(['git', 'clone', '-bgh-pages', repo_url], stdout=logfile, stderr=logfile)
    return repo


def migrate_database(repo, logfile=None, seed=True):
    """ Ugly way of doing database migration """
    if logfile is None:
        logfile = open(os.devnull, 'w')
    # db migration - this is ugly way of doing this
    print '%s: Migrating database' % timestamp()
    # unzip migration files
    zfile = '%s/%s.zip' % (repo, repo)
    subprocess.call(['unzip', '-o', zfile, '-d', repo], stdout=logfile)
    os.chdir('osm-stats-workers/src/db/migrations')
    subprocess.call(['knex', 'migrate:latest'], stdout=logfile)
    if seed:
        subprocess.call(['knex', 'seed:run'], stdout=logfile)
    os.chdir('../../../../')


def add_env(name, repo, logfile=None):
    """ Link env and add to zip """
    if logfile is None:
        logfile = open(os.devnull, 'w')
    # link .env to this file
    if os.path.exists('.env'):
        os.remove('.env')
    os.symlink('%s.env' % name, '.env')
    # add .env file to zip
    subprocess.call(['zip', '%s/%s.zip' % (repo, repo), '-xi', '.env'], stdout=logfile)


def deploy_to_ec2(name, host_string, logfile=None):
    """ Deploy latest docker to EC2 """
    if logfile is None:
        logfile = open(os.devnull, 'w')
    try:
        print '%s: Deploying to EC2' % timestamp()
        sys.stdout = logfile
        with settings(host_string=host_string, key_filename=name + '.pem', connection_attempts=3):
            fabfile.setup_host(name)
            fabfile.copy_files()
        # hack to use new session so user guaranteed part of docker group
        subprocess.call(['fab', 'deploy', '-i%s.pem' % name, '-H %s' % host_string], stdout=logfile)
    finally:
        sys.stdout.close()
        sys.stdout = sys.__stdout__


def read_envs(name):
    """ Read env file and return dict """
    envs = {}
    with open('%s.env' % name, 'r') as f:
        for line in f:
            parts = line.split('=')
            envs[parts[0]] = parts[1]
    return envs

if __name__ == "__main__":
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser0 = argparse.ArgumentParser(description='Deploy OSM Stats', formatter_class=dhf)
    subparser = parser0.add_subparsers(dest='command')

    parser = subparser.add_parser('deploy', help='Deploy OSM Stats', formatter_class=dhf)
    parser.add_argument('--name', help='Base name for all AWS resources', default='osmstats')
    parser.add_argument('--lsize', help='Size (MB) of Lambda function', default=512)
    parser.add_argument('--ltimeout', help='Timeout (seconds) of Lambda function', default=300)
    parser.add_argument('--dbclass', help='The Amazon instance class for the RDS database', default='db.t2.medium')
    parser.add_argument('--ec2class', help='The Amazon instance class for the EC2', default='t2.medium')
    parser.add_argument('--password', help='The password to use for database', required=True)  # default='t3sting9huy')

    parser = subparser.add_parser('update', help='Update OSM Stats with latest code')
    parser.add_argument('--name', help='Base name of deployment', default='osmstats')

    args = parser0.parse_args()

    logfile = open('%s.log' % args.name, 'w')

    if args.command == 'deploy':
        print '%s: Starting deployment of %s' % (timestamp(), args.name)
        repo = clone_workers_repo(logfile)
        # create stream and RDS database
        stream = create_stream(args.name)
        db = create_database(args.name, args.password, dbclass=args.dbclass)
        os.environ['DATABASE_URL'] = db['URL']
        migrate_database(repo, logfile)

        # set up environment variables
        session = boto3._get_default_session()._session
        env = [
            'DEPLOY_NAME=%s' % args.name,
            'KINESIS_STREAM=%s' % args.name,
            'DATABASE_URL=%s' % db['URL'],
            'AWS_REGION=%s' % session.get_config_variable('region'),
            'AWS_ACCESS_KEY_ID=%s' % session.get_credentials().access_key,
            'AWS_SECRET_ACCESS_KEY=%s' % session.get_credentials().secret_key,
        ]
        # create environment variable file
        with open('%s.env' % args.name, 'w') as f:
            [f.write(e + '\n') for e in env]
        add_env(args.name, repo, logfile)
        # create lambda function
        zfile = '%s/%s.zip' % (repo, repo)
        func = create_function(args.name, zfile, lsize=int(args.lsize), timeout=int(args.ltimeout))

        # create mapping to kinesis stream
        batchsz = 1     # for now, this must be one
        l = boto3.client('lambda')
        sources = l.list_event_source_mappings(FunctionName=args.name,
                                               EventSourceArn=stream['StreamARN'])['EventSourceMappings']
        # add if this stream is not already mapped
        if stream['StreamARN'] not in [s['EventSourceArn'] for s in sources]:
            l.create_event_source_mapping(FunctionName=args.name, EventSourceArn=stream['StreamARN'],
                                          BatchSize=batchsz, StartingPosition='TRIM_HORIZON')
        # start up EC2 instance
        ec2_machine = create_ec2(args.name, instancetype=args.ec2class, AMI='ami-60b6c60a') #AMI='ami-63b25203')
        env.append('EC2_URL=%s' % ec2_machine.public_dns_name)
        with open('%s.env' % args.name, 'a') as f:
            f.write(env[-1])
        host_string = 'ec2-user@%s:22' % ec2_machine.public_dns_name
        deploy_to_ec2(args.name, host_string, logfile)

        # update RDS security group to allow EC2 and lambda functions access
        ec2 = boto3.client('ec2')
        groups = ['%s_rds' % args.name, '%s_ec2' % args.name, '%s_lambda' % args.name]
        groups = [g for g in ec2.describe_security_groups(GroupNames=groups)['SecurityGroups']]
        gid = groups[0]['GroupId']
        try:
            ec2.authorize_security_group_ingress(GroupId=gid, SourceSecurityGroupName=groups[1]['GroupName'])
            ec2.authorize_security_group_ingress(GroupId=gid, SourceSecurityGroupName=groups[2]['GroupName'])
            rds = boto3.client('rds')
            import pdb; pdb.set_trace()
            rds.reboot_db_instance(DBInstanceIdentifier=args.name)
        except Exception as e:
            # this likely means the rules already exist
            pass

        print '%s: Completed deployment of %s' % (timestamp(), args.name)

    if args.command == 'update':
        print '%s: Starting updating of %s' % (timestamp(), args.name)
        envs = read_envs(args.name)
        repo = clone_workers_repo(logfile)
        # update database
        os.environ['DATABASE_URL'] = envs['DATABASE_URL']
        migrate_database(repo, logfile, seed=False)
        add_env(args.name, repo, logfile)
        # update lambda function
        zfile = '%s/%s.zip' % (repo, repo)
        func = create_function(args.name, zfile, update=True)
        host_string = 'ec2-user@%s:22' % envs['EC2_URL']
        deploy_to_ec2(args.name, host_string, logfile)
        print '%s: Completed updating of %s' % (timestamp(), args.name)

    logfile.close()
