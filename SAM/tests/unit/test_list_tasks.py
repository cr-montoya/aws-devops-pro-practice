import json
import unittest

from moto import mock_aws

from src.list_task.app import lambda_handler
from tests.unit.helpers import create_tasks_table


class TestListTasks(unittest.TestCase):

    @mock_aws
    def test_list_tasks_empty(self):
        create_tasks_table()

        response = lambda_handler({}, None)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['items'], [])
        self.assertIsNone(body['next_token'])

    @mock_aws
    def test_list_tasks_with_items(self):
        table = create_tasks_table()
        table.put_item(Item={'task_id': 'abc-1', 'title': 'Task 1', 'status': 'PENDING', 'created_at': '2026-04-01'})
        table.put_item(Item={'task_id': 'abc-2', 'title': 'Task 2', 'status': 'DONE', 'created_at': '2026-04-01'})

        response = lambda_handler({}, None)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(len(body['items']), 2)
        self.assertIsNone(body['next_token'])

    @mock_aws
    def test_list_tasks_with_limit_and_next_token(self):
        table = create_tasks_table()
        for index in range(3):
            table.put_item(Item={
                'task_id': f'abc-{index}',
                'title': f'Task {index}',
                'status': 'PENDING',
                'created_at': '2026-04-01'
            })

        first_response = lambda_handler({'queryStringParameters': {'limit': '1'}}, None)
        first_body = json.loads(first_response['body'])

        self.assertEqual(first_response['statusCode'], 200)
        self.assertEqual(len(first_body['items']), 1)
        self.assertIsNotNone(first_body['next_token'])

        second_response = lambda_handler({
            'queryStringParameters': {
                'limit': '1',
                'next_token': first_body['next_token']
            }
        }, None)
        second_body = json.loads(second_response['body'])

        self.assertEqual(second_response['statusCode'], 200)
        self.assertEqual(len(second_body['items']), 1)

    @mock_aws
    def test_list_tasks_rejects_invalid_limit(self):
        create_tasks_table()

        response = lambda_handler({'queryStringParameters': {'limit': '0'}}, None)

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'limit must be between 1 and 100')


if __name__ == '__main__':
    unittest.main()
