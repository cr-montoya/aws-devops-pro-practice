import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))

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
    body = json.loads(event['body'])
    status = body.get('status')

    if not task_id or not status:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'task_id and status are required'})
        }

    if status not in VALID_STATUSES:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'status must be one of {VALID_STATUSES}'})
        }

    existing = table.get_item(Key={'task_id': task_id})
    if not existing.get('Item'):
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Task not found'})
        }

    response = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #s = :status',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':status': status},
        ReturnValues='ALL_NEW'
    )

    return {
        'statusCode': 200,
        'body': json.dumps(response['Attributes'])
    }
