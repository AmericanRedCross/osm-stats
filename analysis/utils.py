#!/usr/bin/env python

import json
import time
import datetime
import pandas as pd
import boto3.session
import re


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


def fetch_stream(name, profile='default'):
    """ Get records from a Kinesis stream """
    session = boto3.session.Session(profile_name=profile)
    kinesis = session.client('kinesis')

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


def parse_lambda_event(event):
    """ Parse JSON event """
    if not isinstance(event['message'], basestring):
        msg = event['message'][0]
    else:
        msg = event['message']

    start = msg.find('RequestId')
    if start > -1:
        requestId = msg[(start+11):start+47]
    else:
        parts = msg.split('\t')
        try:
            # msgtime = parse(parts[0])
            requestId = parts[1]
            msg = ' '.join(parts[2:])
        except Exception:
            return None

    if msg[0:5] == 'START':
        return requestId, {'start_time': event['timestamp']}
    elif msg[0:3] == 'END':
        return requestId, {'end_time': event['timestamp']}
    elif msg[0:6] == 'REPORT':
        duration = None
        d = re.search('Duration:(.*) ms\t', msg)
        duration = d.group(1) if d else None
        return requestId, {
            'report_time': event['timestamp'],
            'duration': float(duration)
        }
    elif msg[0:7] == 'PAYLOAD':
        try:
            payload = json.loads(msg[8:])
            changeset = payload['elements'][0]['changeset']
        except:
            payload = msg[8:]
            changeset = 'unable to parse'
        return requestId, {
            'payload_time': event['timestamp'],
            'payload': payload,
            'changeset': changeset
        }
    elif msg[0:7] == 'SUCCESS':
        return requestId, {
            'success_time': event['timestamp'],
            'success': msg[8:]
        }
    elif msg[0:7] == 'FAILURE':
        return requestId, {
            'failure_time': event['timestamp'],
            'failure': msg[8:]
        }
    # elif msg[0:4] == 'Task':
        # this is a timeout, which does not provide the requestId
    #    return None
    else:
        # print msg[0:10]
        return None


def distill_lambda_logs(filename):
    """ Initialize object with newline delimited JSON log file """
    requests = {}
    i = 0
    with open(filename, 'r') as f:
        line = f.readline()
        while line:
            event = parse_lambda_event(json.loads(line))
            if event is not None:
                requestId = event[0]
                if requestId not in requests.keys():
                    requests[requestId] = {'requestId': requestId, 'runs': 1}
                if 'start_time' in event[1] and 'start_time' in requests[requestId]:
                    requests[requestId]['runs'] = requests[requestId]['runs'] + 1
                requests[requestId].update(event[1])
            line = f.readline()
            i = i + 1
    return requests
