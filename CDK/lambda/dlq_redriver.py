import base64
import json
import os
import boto3
from aws_xray_sdk.core import patch_all

patch_all()

sqs = boto3.client("sqs")
lambda_client = boto3.client("lambda")

DLQ_URL = os.environ["DLQ_URL"]
PROCESSOR_FUNCTION_NAME = os.environ["PROCESSOR_FUNCTION_NAME"]


def handler(event, context):
    redriven = 0
    failed = 0

    response = sqs.receive_message(
        QueueUrl=DLQ_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=0
    )

    messages = response.get("Messages", [])
    if not messages:
        print("DLQ is empty - nothing to redrive")
        return {"redriven": 0, "failed": 0}

    for msg in messages:
        receipt_handle = msg["ReceiptHandle"]
        body = msg["Body"]

        # Reconstruct the Kinesis envelope the processor expects:
        # event["Records"][0]["kinesis"]["data"] must be base64-encoded JSON
        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": base64.b64encode(body.encode()).decode()
                    }
                }
            ]
        }

        try:
            resp = lambda_client.invoke(
                FunctionName=PROCESSOR_FUNCTION_NAME,
                InvocationType="RequestResponse",
                Payload=json.dumps(kinesis_event)
            )
            if resp.get("StatusCode") == 200 and "FunctionError" not in resp:
                sqs.delete_message(QueueUrl=DLQ_URL, ReceiptHandle=receipt_handle)
                redriven += 1
                print(f"Redriven message {msg['MessageId']}")
            else:
                failed += 1
                print(f"Processor error for {msg['MessageId']}: {resp.get('FunctionError')}")
        except Exception as e:
            failed += 1
            print(f"Failed to invoke processor for {msg['MessageId']}: {e}")

    return {"redriven": redriven, "failed": failed}
