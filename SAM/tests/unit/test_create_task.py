import json
import unittest
from unittest.mock import patch

from moto import mock_aws

from src.create_task.app import lambda_handler
from tests.unit.helpers import create_tasks_table


class TestCreateTask(unittest.TestCase):

    @mock_aws
    def test_create_task_success(self):
        create_tasks_table()

        response = lambda_handler({
            'body': json.dumps({'title': 'Learn SAM'})
        }, None)

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        body = json.loads(response['body'])
        self.assertEqual(body['title'], 'Learn SAM')
        self.assertEqual(body['status'], 'PENDING')
        self.assertIn('task_id', body)
        self.assertIn('created_at', body)

    @mock_aws
    def test_create_task_no_title(self):
        create_tasks_table()

        response = lambda_handler({
            'body': json.dumps({})
        }, None)

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Title is required')

    @mock_aws
    def test_create_task_allows_duplicate_title(self):
        create_tasks_table()
        event = {
            'body': json.dumps({'title': 'Learn SAM'})
        }

        response1 = lambda_handler(event, None)
        response2 = lambda_handler(event, None)

        self.assertEqual(response1['statusCode'], 201)
        self.assertEqual(response2['statusCode'], 201)

    @mock_aws
    def test_create_task_generated_id_conflict(self):
        table = create_tasks_table()
        table.put_item(Item={'task_id': 'fixed-id', 'title': 'Existing', 'status': 'PENDING'})

        with patch('src.create_task.app.uuid.uuid4', return_value='fixed-id'):
            response = lambda_handler({
                'body': json.dumps({'title': 'Learn SAM'})
            }, None)

        self.assertEqual(response['statusCode'], 409)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Task already exists')

    @mock_aws
    def test_create_task_invalid_json(self):
        create_tasks_table()

        response = lambda_handler({'body': '{invalid-json'}, None)

        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Request body must be valid JSON')


if __name__ == '__main__':
    unittest.main()
