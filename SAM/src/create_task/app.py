import boto3
import json
import uuid
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))

def lambda_handler(event, context):
    """
    Creates a new task in DynamoDB.

    Request body:
        title (str): Title of the task. Required. Must be unique.

    Returns:
        201: Task created successfully with task details.
        400: Missing required field 'title'.
        409: A task with the same title already exists.
    """
    body = json.loads(event.get('body') or '{}')
    title = body.get('title')

    if not title:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Title is required'})
        }

    response = table.scan(
        FilterExpression='title = :title',
        ExpressionAttributeValues={':title': title}
    )

    if response['Items']:
        return {
            'statusCode': 409,
            'body': json.dumps({'error': 'Title already exists'})
        }

    task_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    table.put_item(
        Item={
            'task_id': task_id,
            'title': title,
            'status': 'PENDING',
            'created_at': created_at
        }
    )

    return {
        'statusCode': 201,
        'body': json.dumps({
            'task_id': task_id, 
            'title': title,
            'status': 'PENDING',
            'created_at': created_at
        })
    }
