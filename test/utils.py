#!/usr/bin/env python

import json
import time
import datetime
import pandas as pd
import boto3


def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def read_nljson(filename):
    """ Read in newline delimited JSON as array of dicts """
    arr = []
    with open(filename, 'r') as f:
        for line in f:
            arr.append(json.loads(line))
    return arr


def write_nljson(data, filename):
    """ Write an array of dicts as newline delimited JSON """
    with open(filename, 'w') as f:
        [f.write(json.dumps(d, default=json_serialize)+'\n') for d in data]


def dicts2DataFrame(dicts):
    """ Convert array of dictionaries to pandas DataFrame """
    df = None
    for j in dicts:
        series = pd.Series.to_frame(pd.Series(j)).T
        if df is None:
            df = series
        else:
            df = df.append(series, ignore_index=True)
    return df


def fetch_stream(name):
    """ Get records from a Kinesis stream """
    kinesis = boto3.client('kinesis')

    records = []
    # get shard ids
    shardids = [s['ShardId'] for s in kinesis.describe_stream(StreamName=name)['StreamDescription']['Shards']]
    for sid in shardids[0:1]:
        # get first iterator
        it = kinesis.get_shard_iterator(
            StreamName=name, ShardId=sid, ShardIteratorType='TRIM_HORIZON')['ShardIterator']
        while True:
            try:
                resp = kinesis.get_records(ShardIterator=it)
                records = records + resp['Records']
                it = resp['NextShardIterator']
                if len(resp['Records']) == 0:
                    break
            except Exception as e:
                print 'Error, %s' % e
                time.sleep(1)
            # avoid ProvisionedThroughputExceededException
            time.sleep(1)
    return records
