#!/usr/bin/env python

import sys
import json
import re






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
