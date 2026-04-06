#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.streaming_stack import StreamingStack

app = cdk.App()
env = cdk.Environment(region="us-east-2")

# Configuration
app_name = "orders"
stage = "dev"
component = "kinesis-archive"

# Stacks
networking = NetworkingStack(
    app, "Networking",
    app_name=app_name,
    stage=stage,
    description="VPC with multi-AZ public subnets and internet gateway",
    env=env
)

storage = StorageStack(
    app, "Storage",
    app_name=app_name,
    stage=stage,
    component=component,
    description="DynamoDB table and S3 bucket for Kinesis Firehose archive",
    env=env
)

streaming = StreamingStack(
    app, "Streaming",
    app_name=app_name,
    stage=stage,
    storage_stack=storage,
    description="Kinesis Data Streams and Firehose for real-time event processing",
    env=env
)

app.synth()
