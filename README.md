# OSM Stats

The deployment script will deploy all services needed to run OSM Stats.  This includes:
    - EC2 instance running planet-stream and osm-stats-api
    - Kinesis stream for planet-stream output
    - Lambda function for osm-stats-worker, ingesting data from Kinesis stream
    - RDS database for osm-stats-worker output
    - Associated roles and security groups

The user running the script should have credentials and a default AWS region configured by using aws configure

## Installation of Deployment Script

Install the Python requirements for the script, and configure AWS credentials and default region

```
$ pip install -r requirements.txt
$ aws configure

# install node according to system then
$ npm install -g knex

# call with help for list of parameters
$ ./osm-stats-deploy.py -h

```

## Deployment

Call the deployment script with a name used to identify all the AWS services created.

```
$ ./osm-stats-deploy.py --name osmstats-mm
```

Information messages will be printed for each step, and the entire process can take up to 15 minutes.   Additional log output from the EC2 instance is saved in a .fabric.log script.

