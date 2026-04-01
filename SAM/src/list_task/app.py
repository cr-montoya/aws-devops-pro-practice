import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'Tasks-${Stage}'))


def lambda_handler(event, context):
    """
    Lists all tasks from DynamoDB.

    Returns:
        200: List of all tasks. Returns empty list if no tasks exist.
    """
    response = table.scan()
    items = response.get('Items', [])

    return {
        'statusCode': 200,
        'body': json.dumps(items)
    }
