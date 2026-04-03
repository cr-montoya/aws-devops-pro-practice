import boto3
import json
import unittest
from moto import mock_aws
from src.get_task.app import lambda_handler


class TestGetTask(unittest.TestCase):

    def _create_table(self):
        # Helper method: Create mock DynamoDB table and return table reference
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        dynamodb.create_table(
            TableName='Tasks-${Stage}',
            KeySchema=[{'AttributeName': 'task_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'task_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        return dynamodb.Table('Tasks-${Stage}')

    @mock_aws
    def test_get_task_success(self):
        # Step 1: Setup - Create table and insert test task
        table = self._create_table()
        table.put_item(Item={
            'task_id': 'abc-123',
            'title': 'Learn SAM',
            'status': 'PENDING',
            'created_at': '2026-04-01T10:00:00'
        })

        # Step 2: Prepare event with task_id
        event = {'pathParameters': {'task_id': 'abc-123'}}

        # Step 3: Call Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['task_id'], 'abc-123')
        self.assertEqual(body['title'], 'Learn SAM')

    @mock_aws
    def test_get_task_not_found(self):
        # Setup - Create table (empty, no items)
        self._create_table()

        # Event with non-existent task_id
        event = {'pathParameters': {'task_id': 'nonexistent'}}

        # Call Lambda handler
        response = lambda_handler(event, None)

        # Assertions - Should return 404
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Task not found')

    @mock_aws
    def test_get_task_missing_task_id(self):
        # Setup - Create table
        self._create_table()

        # Event with missing task_id parameter
        event = {'pathParameters': {}}

        # Call Lambda handler
        response = lambda_handler(event, None)

        # Assertions - Should return 400 (bad request)
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'task_id is required')


if __name__ == '__main__':
    unittest.main()
