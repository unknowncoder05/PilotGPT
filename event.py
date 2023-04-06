import boto3
import json
import datetime
import os


def send_event_aws(event, task_id):
    event_source = os.getenv('EVENT_SOURCE', 'projectc-app.core')
    event_task_detail_type = os.getenv(
        'EVENT_TASK_DETAIL_TYPE', 'task-process')
    region_name = os.getenv('AWS_REGION_NAME')
    client = boto3.client('events', region_name=region_name)

    client.put_events(
        Entries=[
            {
                'Time': datetime.datetime.now(),
                'Source': event_source,
                'DetailType': event_task_detail_type,
                'Detail': json.dumps({
                    'id': task_id,
                }),
            },
        ],
    )
