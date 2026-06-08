#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import aws_cdk as cdk

load_dotenv()  # loads .env if present; no-op if file doesn't exist (e.g. CI/CD)
from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.streaming_stack import StreamingStack
from stacks.processing_stack import ProcessingStack
from stacks.compute_stack import ComputeStack
from stacks.observability_stack import ObservabilityStack
from stacks.incident_response_stack import IncidentResponseStack
from stacks.app_stage import AppStage
from stacks.pipeline_stack import PipelineStack

app = cdk.App()

# --- Configuration (see .env.example) ---
aws_region  = os.environ.get("AWS_REGION", "us-east-2")
app_name    = os.environ.get("APP_NAME", "orders")
stage       = os.environ.get("STAGE", "dev")
component   = os.environ.get("COMPONENT", "kinesis-archive")
alert_emails = [e.strip() for e in os.environ.get("ALERT_EMAILS", "").split(",") if e.strip()]

env = cdk.Environment(region=aws_region)

# --- Individual stacks (for direct cdk deploy during development) ---

networking = NetworkingStack(
    app, "Networking",
    app_name=app_name,
    stage=stage,
    description="VPC with public/private isolated subnets and VPC Endpoints for ECR, S3, Secrets Manager, Logs, Kinesis (prod only)",
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

processing = ProcessingStack(
    app, "Processing",
    app_name=app_name,
    stage=stage,
    streaming_stack=streaming,
    storage_stack=storage,
    description="Lambda stream processor (KDS -> DynamoDB) with SQS DLQ and X-Ray tracing",
    env=env
)

compute = ComputeStack(
    app, "Compute",
    app_name=app_name,
    stage=stage,
    networking_stack=networking,
    storage_stack=storage,
    streaming_stack=streaming,
    description="ECS Fargate service with FastAPI admin panel and ALB",
    env=env
)

observability = ObservabilityStack(
    app, "Observability",
    app_name=app_name,
    stage=stage,
    processing_stack=processing,
    streaming_stack=streaming,
    storage_stack=storage,
    compute_stack=compute,
    alert_emails=alert_emails,
    description="CloudWatch alarms, dashboard, log retention, and X-Ray for orders pipeline",
    env=env
)
observability.add_dependency(processing)
observability.add_dependency(compute)

incident_response = IncidentResponseStack(
    app, "IncidentResponse",
    app_name=app_name,
    stage=stage,
    processing_stack=processing,
    observability_stack=observability,
    compute_stack=compute,
    description="EventBridge rules, SNS alerts, and DLQ auto-remediation Lambda",
    env=env
)
incident_response.add_dependency(observability)

# --- Pipeline stack (self-mutating CDK Pipeline for dev -> prod) ---
# Prerequisites (see .env.example):
#   1. Set GITHUB_OWNER, ALERT_EMAILS, CODESTAR_CONNECTION_ARN in your .env
#   2. Create a GitHub CodeStar Connection in AWS Console and set it to "Available"
#   3. Run `cdk deploy Pipeline` once manually — after that, pushes to main trigger it automatically
pipeline = PipelineStack(
    app, "Pipeline",
    github_owner=os.environ.get("GITHUB_OWNER", "GITHUB_OWNER_NOT_SET"),
    github_repo=app.node.try_get_context("github_repo"),
    github_branch=app.node.try_get_context("github_branch"),
    codestar_connection_arn=os.environ.get("CODESTAR_CONNECTION_ARN", "CODESTAR_CONNECTION_ARN_NOT_SET"),
    app_name=app_name,
    component=component,
    dev_alert_emails=alert_emails,
    prod_alert_emails=alert_emails,
    description="Self-mutating CDK Pipeline: GitHub -> dev -> manual approval -> prod",
    env=env
)

app.synth()
