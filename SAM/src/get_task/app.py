import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))


def lambda_handler(event, context):
    """
    Retrieves a single task from DynamoDB by task_id.

    Path parameters:
        task_id (str): The unique identifier of the task.

    Returns:
        200: Task found and returned successfully.
        400: Missing required path parameter 'task_id'.
        404: No task found with the given task_id.
    """
    path_params = event.get('pathParameters') or {}
    task_id = path_params.get('task_id')

    if not task_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'task_id is required'})
        }

    response = table.get_item(Key={'task_id': task_id})
    item = response.get('Item')

    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Task not found'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps(item)
    }
