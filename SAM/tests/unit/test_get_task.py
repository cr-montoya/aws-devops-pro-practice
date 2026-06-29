import json
import unittest

from moto import mock_aws

from src.get_task.app import lambda_handler
from tests.unit.helpers import create_tasks_table


class TestGetTask(unittest.TestCase):

    @mock_aws
    def test_get_task_success(self):
        table = create_tasks_table()
        table.put_item(Item={
            'task_id': 'abc-123',
            'title': 'Learn SAM',
            'status': 'PENDING',
            'created_at': '2026-04-01T10:00:00'
        })

        response = lambda_handler({'pathParameters': {'task_id': 'abc-123'}}, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        body = json.loads(response['body'])
        self.assertEqual(body['task_id'], 'abc-123')
        self.assertEqual(body['title'], 'Learn SAM')

    @mock_aws
    def test_get_task_not_found(self):
        create_tasks_table()

        response = lambda_handler({'pathParameters': {'task_id': 'nonexistent'}}, None)

        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Task not found')

    @mock_aws
    def test_get_task_missing_task_id(self):
        create_tasks_table()

        response = lambda_handler({'pathParameters': {}}, None)

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'task_id is required')


if __name__ == '__main__':
    unittest.main()
