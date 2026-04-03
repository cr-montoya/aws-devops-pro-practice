import json
import unittest

from src.health_check.app import lambda_handler

class TestHealthCheck(unittest.TestCase):

    def test_health_check_returns_200(self):
        # Step 1: Prepare empty event (health check doesn't need input)
        event = {}
        context = None

        # Step 2: Call the Lambda handler
        response = lambda_handler(event, context)

        # Step 3: Assertions
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "All systems operational")
