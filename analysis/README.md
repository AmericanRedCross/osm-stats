# Analyzing Mapathon data

## Typical usage
On a typical day without a mapathon there are on average X changesets, that are split between Y records (planet-stream splits large changesets up into smaller records containing no more than 20 changes).

## Getting and putting data from Kinesis stream

After a mapathon, the included iPython Notebook OSMStats.ipynb can be used to analyze the data from the last 24 hours.  The notebook can be run interactively to download data from Kinesis and logs from the Lambda function.

To later put those records back into a kinesis stream for testing purposes, use the AWS CLI:

	$ while read line; do aws kinesis put-record --partition-key '0' --stream-name osmstats --data "$line"; done < filename.nljson

Which will put the records into a kinesis stream called osmstats (which must exist). A single partition-key for all records will put them in the same shard.


## Download worker logs

The logs from the Lambda osm-stats-worker function can be downloaded using [awslogs](https://github.com/jorgebastida/awslogs). The download the logs for the last day:

	$ pip install awslogs
	$ awslogs get /aws/lambda/osm-stats-worker ALL --timestamp --ingestion-time --start='1d' > lambdalogs.json



