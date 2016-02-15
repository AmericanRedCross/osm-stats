#!/usr/bin/env python

import sys
import json
import re


def parse_event(event):
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
            event = parse_event(json.loads(line))
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


"""
    obsolete function.   use awslog: https://github.com/jorgebastida/awslogss
    Example:
        $ awslogs get /aws/lambda/osm-gamification-worker ALL --timestamp --ingestion-time --start='1w' > dump.json

    @classmethod
    def download_logs(cls, loggroupname):
        # Download all logs in log group and return as newline-delimited JSON
        client = boto3.client('logs')
        events = []

        def get_log_events(logGroupName, logStreamName):
            events = []
            nextToken = ''
            kwargs = {}
            while True:
                logs = client.get_log_events(logGroupName=loggroupname,
                    logStreamName=streamname, **kwargs)
                events.append(logs['events'])
                nextToken = logs['nextForwardToken']
                print logs['nextForwardToken'], logs['nextBackwardToken']
                if nextToken is '':
                    break
            return events

        for stream in client.describe_log_streams(logGroupName=loggroupname)['logStreams'][0:1]:
            streamname = stream['logStreamName']
            for event in get_log_events(loggroupname, streamname):
                msg = event['message']
                msgtime = None
                if msg[0:5] == 'START' or msg[0:3] == 'END' or msg[0:6] == 'REPORT':
                    start = msg.find('RequestId')+10
                    requestId = msg[start:start+37]
                elif msg[0:4] == 'Task':
                    # this is a timeout
                    requestId = None
                else:
                    parts = msg.split('\t')
                    try:
                        msgtime = parse(parts[0])
                    except Exception, e:
                        continue
                        # sys.stderr.write('ERROR: ' + parts[0])
                    requestId = parts[1]
                    msg = ' '.join(parts[2:])
                ev = {
                    'ingestionTime': str(datetime.datetime.fromtimestamp(event['ingestionTime']/1000)),
                    'timestamp': str(datetime.datetime.fromtimestamp(event['ingestionTime']/1000)),
                    'msgtime': str(msgtime),
                    'message': msg,
                    'requestId': requestId,
                }
                events.append(ev)
        return events

"""

if __name__ == "__main__":
    for request in distill_lambda_logs(sys.argv[1]).values():
        print json.dumps(request)
