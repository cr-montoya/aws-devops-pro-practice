import json
import unittest

from src.health_check.app import lambda_handler

class TestHealthCheck(unittest.TestCase):

    def test_health_check_returns_200(self):
        event = {}
        context = None

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "All systems operational")
