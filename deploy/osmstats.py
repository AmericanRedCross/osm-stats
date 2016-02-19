#!/usr/bin/env python

import os
import sys
import argparse
import boto3
import subprocess
from boto3utils import timestamp, create_stream, create_function, create_database, create_ec2
from fabric.api import settings
import fabfile

'''
    OSM Stats AWS deployment script
'''


if __name__ == "__main__":
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser0 = argparse.ArgumentParser(description='Deploy OSM Stats', formatter_class=dhf)
    parser0.add_argument('--name', help='Base name for all AWS resources', default='osmstats')
    parser0.add_argument('--lsize', help='Size (MB) of Lambda function', default=512)
    parser0.add_argument('--ltimeout', help='Timeout (seconds) of Lambda function', default=10)
    parser0.add_argument('--update', help='Update with latest code', default=False)
    parser0.add_argument('--dbclass', help='The Amazon instance class for the RDS database', default='db.t2.medium')
    parser0.add_argument('--password', help='The password to use for database', required=True)  # default='t3sting9huy')

    args = parser0.parse_args()
    print '%s: Starting deployment of %s' % (timestamp(), args.name)

    # clone/ workers repo and create zip
    repo = 'osm-stats-workers'
    repo_url = 'https://github.com/AmericanRedCross/osm-stats-workers.git'
    logfile = open('%_deploy.log' % args.name, 'w')
    if not os.path.exists(repo):
        print '%s: Cloning %s repository' % (timestamp(), repo)
        subprocess.call(['git', 'clone', '-bgh-pages', repo_url], stdout=logfile)
    zfile = 'osm-stats-workers/osm-stats-workers.zip'

    # create stream and RDS database
    stream = create_stream(args.name)
    db = create_database(args.name, args.password, dbclass=args.dbclass)

    # database migration
    migrate = True
    if migrate:
        # db migration - this is ugly way of doing this
        print '%s: Migrating database' % timestamp()
        # unzip migration files
        subprocess.call(['unzip', '-o', zfile, '-d', repo], stdout=logfile)
        os.chdir('osm-stats-workers/src/db/migrations')
        subprocess.call(['knex', 'migrate:latest'], stdout=logfile)
        #subprocess.call(['knex', 'seed:run'], stdout=logfile)
        os.chdir('../../../../')

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
    # link .env to this file
    if os.path.exists('.env'):
        os.remove('.env')
    os.symlink('%s.env' % args.name, '.env')
    # add .env file to zip
    subprocess.call(['zip', '%s/%s.zip' % (repo, repo), '-xi', '.env'], stdout=logfile)

    # create or update lambda function
    func = create_function(args.name, zfile, lsize=args.lsize, timeout=args.ltimeout, update=args.update)

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
    ec2 = create_ec2(args.name)
    env.append('EC2_URL=%s' % ec2.public_dns_name)
    with open('%s.env' % args.name, 'a') as f:
        f.write(env[-1])
    host_string = 'ec2-user@%s:22' % ec2.public_dns_name

    # configure EC2
    try:
        print '%s: Deploying to EC2' % timestamp()
        sys.stdout = logfile
        with settings(host_string=host_string, key_filename=args.name + '.pem', connection_attempts=3):
            fabfile.setup_host()
            fabfile.copy_files()
        # hack to use new session so user guaranteed part of docker group
        subprocess.call(['fab', 'deploy', '-i%s.pem' % args.name, '-H %s' % host_string], stdout=logfile)
    finally:
        sys.stdout.close()
        sys.stdout = sys.__stdout__
    logfile.close()

    # docker compose up
    print '%s: Completed deployment of %s' % (timestamp(), args.name)
    [sys.stdout.write('\t%s\n' % e) for e in env]
