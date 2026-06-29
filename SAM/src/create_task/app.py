import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

try:
    from common.http import json_response, parse_json_body
except ModuleNotFoundError:
    from src.common.http import json_response, parse_json_body


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_table():
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))


def lambda_handler(event, context):
    """
    Creates a new task in DynamoDB.

    Request body:
        title (str): Title of the task. Required.

    Returns:
        201: Task created successfully with task details.
        400: Missing required field 'title'.
        409: A task with the same generated task_id already exists.
    """
    body, error_response = parse_json_body(event)
    if error_response:
        return error_response

    title = body.get('title')

    if not title:
        return json_response(400, {'error': 'Title is required'})

    task_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    item = {
        'task_id': task_id,
        'title': title,
        'status': 'PENDING',
        'created_at': created_at
    }
    table = get_table()

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(task_id)'
        )
    except ClientError as error:
        if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return json_response(409, {'error': 'Task already exists'})
        logger.exception('Failed to create task')
        return json_response(500, {'error': 'Internal server error'})

    return json_response(201, item)
