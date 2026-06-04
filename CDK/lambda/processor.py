import base64
import json
import os
import boto3
from aws_xray_sdk.core import patch_all

patch_all()

dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    """
    Stream processor: KDS → DynamoDB

    Reads batch of Kinesis records, decodes base64 JSON, and writes to DynamoDB.
    X-Ray tracing enabled via patch_all().
    """
    table = dynamodb.Table(os.environ["TABLE_NAME"])
    processed = 0

    for record in event["Records"]:
        # Decode base64 Kinesis data
        payload = base64.b64decode(record["kinesis"]["data"])
        order = json.loads(payload)

        # Write to DynamoDB (id is the partition key)
        table.put_item(Item={
            "id": order["order_id"],
            "item": order["item"],
            "qty": order["qty"],
            "timestamp": order["timestamp"],
        })
        processed += 1

    return {
        "statusCode": 200,
        "processed": processed,
    }
