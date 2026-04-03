import boto3
import json
import unittest
from moto import mock_aws
from src.list_task.app import lambda_handler


class TestListTasks(unittest.TestCase):

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
    def test_list_tasks_empty(self):
        # Step 1: Setup - Create empty table
        self._create_table()

        # Step 2: Call Lambda handler with empty event
        response = lambda_handler({}, None)

        # Step 3: Assertions - Should return empty list
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body, [])

    @mock_aws
    def test_list_tasks_with_items(self):
        # Step 1: Setup - Create table and insert multiple tasks
        table = self._create_table()
        table.put_item(Item={'task_id': 'abc-1', 'title': 'Task 1', 'status': 'PENDING', 'created_at': '2026-04-01'})
        table.put_item(Item={'task_id': 'abc-2', 'title': 'Task 2', 'status': 'DONE', 'created_at': '2026-04-01'})

        # Step 2: Call Lambda handler
        response = lambda_handler({}, None)

        # Step 3: Assertions - Should return list with 2 items
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(len(body), 2)


if __name__ == '__main__':
    unittest.main()
