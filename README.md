# OSM Stats

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

When completed the script will print a series of environment variables and also write them to an environment file called "name.env". Make note of the EC2_URL variable and use it below to finish deployment.

```
# change permissions of private key
$ chmod 400 osmstats-mm.pem
$ fabfile deploy -i osmstats-mm.pem $EC2_URL
```



