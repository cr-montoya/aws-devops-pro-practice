import boto3


TABLE_NAME = 'Tasks-${Stage}'


def create_tasks_table():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {'AttributeName': 'task_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'task_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    return dynamodb.Table(TABLE_NAME)
