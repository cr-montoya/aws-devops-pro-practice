import boto3
import json
import unittest
from moto import mock_aws
from src.create_task.app import lambda_handler


class TestCreateTask(unittest.TestCase):

    @mock_aws
    def test_create_task_success(self):
        # Step 1: Setup - Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        dynamodb.create_table(
            TableName='Tasks-${Stage}',
            KeySchema=[
                {'AttributeName': 'task_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'task_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Step 2: Prepare the Lambda event
        event = {
            'body': json.dumps({'title': 'Learn SAM'})
        }

        # Step 3: Call the Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions
        self.assertEqual(response['statusCode'], 201)
        body = json.loads(response['body'])
        self.assertEqual(body['title'], 'Learn SAM')
        self.assertEqual(body['status'], 'PENDING')
        self.assertIn('task_id', body)
        self.assertIn('created_at', body)

    @mock_aws
    def test_create_task_no_title(self):
        # Setup - Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        dynamodb.create_table(
            TableName='Tasks-${Stage}',
            KeySchema=[
                {'AttributeName': 'task_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'task_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Event without title
        event = {
            'body': json.dumps({})
        }

        # Call Lambda handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Title is required')

    @mock_aws
    def test_create_task_duplicate_title(self):
        # Setup - Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        dynamodb.create_table(
            TableName='Tasks-${Stage}',
            KeySchema=[
                {'AttributeName': 'task_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'task_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Event 1: Create "Learn SAM"
        event = {
            'body': json.dumps({'title': 'Learn SAM'})
        }
        response1 = lambda_handler(event, None)
        self.assertEqual(response1['statusCode'], 201)

        # Event 2: Try to create "Learn SAM" again
        response2 = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response2['statusCode'], 409)
        body = json.loads(response2['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], 'Title already exists')


if __name__ == '__main__':
    unittest.main()