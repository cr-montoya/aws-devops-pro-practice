# Orders Platform - Real-time Event Processing with CDK

AWS CDK project for practicing ECS, Kinesis, DynamoDB, and event-driven architecture for DOP-C02 exam preparation.

## Project Structure

```
CDK/
├── app.py                              # Entry point — instantiates all stacks
├── cdk.json                            # CDK configuration
├── requirements.txt                    # Production dependencies (aws-cdk-lib, constructs)
├── requirements-dev.txt                # Dev dependencies (pytest, pytest-cov)
├── stacks/
│   ├── networking_stack.py             # VPC, subnets, NACLs, VPC Endpoints (prod)
│   ├── storage_stack.py                # DynamoDB (PAY_PER_REQUEST) + S3
│   ├── streaming_stack.py              # Kinesis Data Streams + Firehose -> S3
│   ├── processing_stack.py             # Lambda processor + SQS DLQ (on_failure)
│   ├── compute_stack.py                # ECS Fargate + ALB + FastAPI + Secrets Manager
│   ├── observability_stack.py          # CloudWatch Alarms, Dashboard, Log Retention, SNS
│   └── incident_response_stack.py      # EventBridge rules + DLQ re-driver Lambda
├── lambda/
│   ├── processor.py                    # KDS stream processor -> DynamoDB (X-Ray)
│   ├── dlq_redriver.py                 # Re-drives DLQ messages back to processor
│   └── requirements.txt                # aws-xray-sdk (bundled via BundlingOptions)
├── ecs/
│   ├── app.py                          # FastAPI: GET /health, POST /orders
│   ├── Dockerfile                      # Python 3.12-slim, non-root user
│   └── requirements.txt                # fastapi, uvicorn, boto3 (pinned)
└── tests/unit/
    ├── conftest.py                      # Shared pytest fixtures (session-scoped stack graph)
    ├── test_networking_stack.py
    ├── test_storage_stack.py
    ├── test_streaming_stack.py
    ├── test_processing_stack.py
    ├── test_compute_stack.py
    ├── test_observability_stack.py
    └── test_incident_response_stack.py
```

## Setup

```bash
# Activate virtualenv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Bootstrap CDK (one-time per account/region)
cdk bootstrap aws://ACCOUNT_ID/us-east-2
```

## Commands

```bash
# Verify CloudFormation generation
cdk synth

# Run unit tests
pytest tests/unit/ -v

# View differences before deploying
cdk diff

# Deploy all stacks
cdk deploy --all --require-approval never

# Deploy a single stack
cdk deploy Processing

# Destroy all stacks
cdk destroy --all

# List all stacks
cdk ls
```

## Architecture

```
Internet
  └── ALB (public subnet)
        └── ECS Fargate - FastAPI (private subnet in prod, public in dev)
              └── POST /orders -> KDS

KDS
  ├── Lambda processor (on_failure -> SQS DLQ) -> DynamoDB
  └── Kinesis Firehose -> S3 (raw archive, partitioned by date)

CloudWatch
  ├── Alarms: Lambda errors/duration/throttles, KDS iterator age, DLQ depth, ALB 5xx
  ├── Dashboard: orders-dev-dashboard
  └── Log retention: Lambda + ECS (30 days)

SNS: orders-dev-alerts
  ├── Email subscriptions (configured in app.py)
  └── Receives from: all CloudWatch alarms + EventBridge rules

EventBridge
  ├── ECS task stopped -> SNS alert
  ├── Every 5 min -> DLQ re-driver Lambda
  └── Every 15 min -> SNS heartbeat
```

## Environment Configuration

All configuration lives in `app.py`:

```python
app_name = "orders"
stage    = "dev"       # change to "prod" to activate full production setup
component = "kinesis-archive"
alert_emails = ["your@email.com"]
```

Resource naming pattern: `{app_name}-{stage}-{resource}` (e.g. `orders-dev-processor`)

### dev vs prod behavior

| | dev | prod |
|---|---|---|
| VPC subnets | Public only | Public + private isolated |
| ECS task placement | Public subnet, public IP | Private subnet, no public IP |
| VPC Endpoints | None | ECR, ECR Docker, Secrets Manager, CloudWatch Logs, Kinesis (interface) + S3, DynamoDB (gateway) |
| NACLs | Public only | Public + private |

## Implementation Status

✅ **Networking** — VPC multi-AZ, NACLs, prod/dev conditional (private subnets + VPC Endpoints in prod)
✅ **Storage** — DynamoDB PAY_PER_REQUEST + S3 for Firehose archive
✅ **Streaming** — KDS (ON_DEMAND, 24h retention) + Firehose -> S3 with date partitioning
✅ **Compute** — ECS Fargate + ALB + FastAPI admin panel + Secrets Manager API key
✅ **Processing** — Lambda processor (KDS -> DynamoDB), SQS DLQ via `on_failure` on event source mapping, X-Ray tracing
✅ **Observability** — 6 CloudWatch alarms, unified dashboard, log retention, SNS topic with email subscriptions
✅ **Incident Response** — EventBridge (ECS stopped, DLQ poll, heartbeat), DLQ re-driver Lambda
⏳ **Pipeline** — CDK Pipelines CI/CD (dev -> prod) — pending

## AWS Domains Covered

| Domain | Coverage |
|---|---|
| D1 - SDLC | CDK IaC, multi-environment, conditional infrastructure |
| D2 - Config Management | L2 constructs, cross-stack references, BundlingOptions |
| D3 - Resilient Solutions | Multi-AZ VPC, DynamoDB PAY_PER_REQUEST, KDS retention, SQS DLQ, bisect_batch_on_error |
| D4 - Monitoring | CloudWatch alarms, dashboard, log retention, X-Ray tracing |
| D5 - Incident Response | EventBridge event patterns, scheduled rules, auto-remediation Lambda |
| D6 - Security | Secrets Manager, IAM least privilege, VPC Endpoints, NACLs, non-root container |
