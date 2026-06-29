import json
import unittest

from moto import mock_aws

from src.update_task.app import lambda_handler
from tests.unit.helpers import create_tasks_table


class TestUpdateTask(unittest.TestCase):

    @mock_aws
    def test_update_task_success(self):
        table = create_tasks_table()
        table.put_item(Item={'task_id': 'abc-123', 'title': 'Learn SAM', 'status': 'PENDING', 'created_at': '2026-04-01'})

        response = lambda_handler({
            'pathParameters': {'task_id': 'abc-123'},
            'body': json.dumps({'status': 'DONE'})
        }, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        body = json.loads(response['body'])
        self.assertEqual(body['status'], 'DONE')

    @mock_aws
    def test_update_task_invalid_status(self):
        create_tasks_table()

        response = lambda_handler({
            'pathParameters': {'task_id': 'abc-123'},
            'body': json.dumps({'status': 'INVALID'})
        }, None)

        self.assertEqual(response['statusCode'], 400)

    @mock_aws
    def test_update_task_not_found(self):
        create_tasks_table()

        response = lambda_handler({
            'pathParameters': {'task_id': 'nonexistent'},
            'body': json.dumps({'status': 'DONE'})
        }, None)

        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Task not found')

    @mock_aws
    def test_update_task_missing_fields(self):
        create_tasks_table()

        response = lambda_handler({
            'pathParameters': {},
            'body': json.dumps({})
        }, None)

        self.assertEqual(response['statusCode'], 400)

    @mock_aws
    def test_update_task_invalid_json(self):
        create_tasks_table()

        response = lambda_handler({
            'pathParameters': {'task_id': 'abc-123'},
            'body': '{invalid-json'
        }, None)

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Request body must be valid JSON')


if __name__ == '__main__':
    unittest.main()
