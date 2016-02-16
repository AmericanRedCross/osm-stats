# OSM Stats


<img width="910" alt="osm-stats" src="https://cloud.githubusercontent.com/assets/719357/13054401/b85f72ce-d3d7-11e5-939a-537fbbfa21bc.png">

The deployment script will deploy all services needed to run OSM Stats.  

This includes:
- EC2 instance running `planet-stream`, `osm-stats-api` and a trending hashtags processor
- Kinesis stream for `planet-stream` output
- Lambda function for `osm-stats-worker`, ingesting data from Kinesis stream
- RDS database for `osm-stats-worker` output
- Associated roles and security groups

The user running the script should have credentials and a default AWS region configured by using aws configure

## Installation of Deployment Script

Install the Python requirements for the script, and configure AWS credentials and default region

```sh
$ pip install -r requirements.txt
$ aws configure

# install node according to system then
$ npm install -g knex

# call with help for list of parameters
$ ./osm-stats-deploy.py -h

```

## Deployment

Call the deployment script with a name used to identify all the AWS services created.

```sh
$ ./osm-stats-deploy.py --name osmstats-mm
```

Where `--name` defines the name of the deployment and used for the naming and tagging of the services. Information messages will be printed for each step, and the entire process can take up to 15 minutes.   Additional log output for the Deployment to EC2 step is saved in a `.fabric.log` script.


## Accessing the EC2 instance

A file containing a private key to access the EC2 instance will be created with the chosen deployment name given above. Do not lose this file, as there is no easy way to regain access to the instance.   To ssh in:

	$ ssh -i DEPLOYMENTNAME.pem ec2-user@EC2URL

Where `DEPLOYMENTNAME` is the name of this deployment and `EC2URL` is the URL of the EC2 output by the script after deployment.
