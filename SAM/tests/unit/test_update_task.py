import boto3
import json
import unittest
from moto import mock_aws
from src.update_task.app import lambda_handler


class TestUpdateTask(unittest.TestCase):

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
    def test_update_task_success(self):
        # Step 1: Setup - Create table and insert task with PENDING status
        table = self._create_table()
        table.put_item(Item={'task_id': 'abc-123', 'title': 'Learn SAM', 'status': 'PENDING', 'created_at': '2026-04-01'})

        # Step 2: Prepare event with task_id and new status
        event = {
            'pathParameters': {'task_id': 'abc-123'},
            'body': json.dumps({'status': 'DONE'})
        }

        # Step 3: Call Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions - Should return updated task with DONE status
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['status'], 'DONE')

    @mock_aws
    def test_update_task_invalid_status(self):
        # Step 1: Setup - Create table
        self._create_table()

        # Step 2: Prepare event with invalid status value
        event = {
            'pathParameters': {'task_id': 'abc-123'},
            'body': json.dumps({'status': 'INVALID'})
        }

        # Step 3: Call Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions - Should return 400 (bad request)
        self.assertEqual(response['statusCode'], 400)

    @mock_aws
    def test_update_task_not_found(self):
        # Step 1: Setup - Create empty table
        self._create_table()

        # Step 2: Prepare event with non-existent task_id
        event = {
            'pathParameters': {'task_id': 'nonexistent'},
            'body': json.dumps({'status': 'DONE'})
        }

        # Step 3: Call Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions - Should return 404
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Task not found')

    @mock_aws
    def test_update_task_missing_fields(self):
        # Step 1: Setup - Create table
        self._create_table()

        # Step 2: Prepare event with missing task_id and status
        event = {
            'pathParameters': {},
            'body': json.dumps({})
        }

        # Step 3: Call Lambda handler
        response = lambda_handler(event, None)

        # Step 4: Assertions - Should return 400 (bad request)
        self.assertEqual(response['statusCode'], 400)


if __name__ == '__main__':
    unittest.main()
