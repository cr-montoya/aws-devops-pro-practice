import logging
import os

import boto3

try:
    from common.http import json_response, parse_json_body
except ModuleNotFoundError:
    from src.common.http import json_response, parse_json_body


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_table():
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))

VALID_STATUSES = ['PENDING', 'DONE']


def lambda_handler(event, context):
    """
    Updates the status of an existing task in DynamoDB.

    Request body:
        task_id (str): The unique identifier of the task. Required.
        status  (str): New status for the task. Must be 'PENDING' or 'DONE'. Required.

    Returns:
        200: Task updated successfully with updated task details.
        400: Missing required fields or invalid status value.
        404: No task found with the given task_id.
    """
    task_id = (event.get('pathParameters') or {}).get('task_id')
    body, error_response = parse_json_body(event)
    if error_response:
        return error_response

    status = body.get('status')

    if not task_id or not status:
        return json_response(400, {'error': 'task_id and status are required'})

    if status not in VALID_STATUSES:
        return json_response(400, {'error': f'status must be one of {VALID_STATUSES}'})

    table = get_table()
    existing = table.get_item(Key={'task_id': task_id})
    if not existing.get('Item'):
        return json_response(404, {'error': 'Task not found'})

    response = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #s = :status',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':status': status},
        ReturnValues='ALL_NEW'
    )

    logger.info('Task status updated', extra={'task_id': task_id, 'status': status})
    return json_response(200, response['Attributes'])
