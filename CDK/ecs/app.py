import os
import json
import uuid
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
import boto3

app = FastAPI()

# Initialize AWS clients
kinesis_client = boto3.client("kinesis")
secrets_client = boto3.client("secretsmanager")

# Environment configuration
STREAM_NAME = os.getenv("STREAM_NAME")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
SECRET_ARN = os.getenv("SECRET_ARN")

# Load API key from Secrets Manager at startup
API_KEY = None

def load_api_key():
    global API_KEY
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_ARN)
        API_KEY = response["SecretString"].strip()
    except Exception as e:
        print(f"Error loading API key: {e}")
        API_KEY = None


# Request/Response models
class Order(BaseModel):
    item: str
    qty: int


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    load_api_key()
    print(f"API initialized. Stream: {STREAM_NAME}, Region: {AWS_REGION}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/orders")
async def create_order(order: Order, x_api_key: str = Header(None)):
    # Validate API key
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    # Generate order ID
    order_id = str(uuid.uuid4())

    # Prepare event for KDS
    event = {
        "order_id": order_id,
        "item": order.item,
        "qty": order.qty,
        "timestamp": str(uuid.uuid4())  # simplified, use datetime in production
    }

    # Publish to Kinesis Data Streams
    try:
        kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(event),
            PartitionKey=order_id
        )
        return OrderResponse(
            order_id=order_id,
            status="accepted",
            message="Order published to stream"
        )
    except Exception as e:
        print(f"Error publishing to Kinesis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish order"
        )
