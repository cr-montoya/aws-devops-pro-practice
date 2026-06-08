# Orders Platform - Real-time Event Processing with CDK

AWS CDK project for practicing ECS, Kinesis, DynamoDB, and event-driven architecture for DOP-C02 exam preparation.

## Project Structure

```
CDK/
├── app.py                              # Entry point — instantiates all stacks
├── cdk.json                            # CDK configuration + pipeline context (repo, branch)
├── .env.example                        # Template for local environment variables
├── requirements.txt                    # Production dependencies (aws-cdk-lib, constructs)
├── requirements-dev.txt                # Dev dependencies (pytest, pytest-cov, python-dotenv)
├── stacks/
│   ├── networking_stack.py             # VPC, subnets, NACLs, VPC Endpoints (prod)
│   ├── storage_stack.py                # DynamoDB (PAY_PER_REQUEST) + S3
│   ├── streaming_stack.py              # Kinesis Data Streams + Firehose -> S3
│   ├── processing_stack.py             # Lambda processor + SQS DLQ (on_failure)
│   ├── compute_stack.py                # ECS Fargate + ALB + FastAPI + Secrets Manager
│   ├── observability_stack.py          # CloudWatch Alarms, Dashboard, Log Retention, SNS
│   ├── incident_response_stack.py      # EventBridge rules + DLQ re-driver Lambda
│   ├── app_stage.py                    # Groups all app stacks for pipeline deployment
│   └── pipeline_stack.py               # Self-mutating CDK Pipeline (dev -> prod)
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

## First-time Setup (Pipeline Workflow)

This project uses CDK Pipelines — after the initial setup, every push to the configured branch triggers an automatic deployment. You only run `cdk deploy` once.

### Step 1 — Clone and install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/aws-devops-pro-practice
cd aws-devops-pro-practice/CDK

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Step 2 — Configure local environment

```bash
cp .env.example .env
# Edit .env with your AWS region and any optional overrides
```

### Step 3 — Bootstrap CDK (one-time per account/region)

```bash
cdk bootstrap
```

### Step 4 — Create SSM parameters (one-time, account-specific)

The pipeline reads personal/account-specific values from SSM so they never appear in the repo:

```bash
aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/github_owner" \
  --value "your-github-username" --type "String"

aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/codestar_connection_arn" \
  --value "arn:aws:codeconnections:us-east-2:ACCOUNT_ID:connection/..." --type "String"

aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/alert_emails" \
  --value "your@email.com" --type "String"
```

### Step 5 — Create a GitHub CodeStar Connection

Go to **AWS Console → CodePipeline → Settings → Connections → Create connection**.
Select GitHub, complete the OAuth flow, and set the status to **Available**.
Copy the ARN into the SSM parameter created in Step 4.

### Step 6 — Deploy the pipeline (one-time)

```bash
cdk deploy Pipeline
```

This creates the CodePipeline infrastructure. From this point on, **every push to the configured branch triggers a full deployment automatically**.

The pipeline flow:
```
push to branch
  └── Synth (cdk synth)
        └── UnitTests (pytest) ← blocks deploy if tests fail
              └── Dev stage (automatic)
                    └── Manual approval
                          └── Prod stage
```

---

## Development Workflow (after setup)

```bash
# Make changes to stacks or application code
# Run tests locally before pushing
pytest tests/unit/ -v

# Verify CloudFormation generation
cdk synth

# Push — the pipeline handles the rest
git push
```

### Deploying individual stacks directly (optional, for faster iteration)

```bash
# Deploy a single stack without going through the pipeline
cdk deploy Processing

# View differences before deploying
cdk diff Networking

# Destroy all directly-deployed stacks
cdk destroy --all
```

> **Note:** Stacks deployed directly (`cdk deploy`) have different CloudFormation names than stacks deployed via the pipeline (`Pipeline-Dev-*`). They coexist independently.

---

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
  ├── Email subscriptions (configured via SSM /orders/pipeline/alert_emails)
  └── Receives from: all CloudWatch alarms + EventBridge rules

EventBridge
  ├── ECS task stopped -> SNS alert
  ├── Every 5 min -> DLQ re-driver Lambda
  └── Every 15 min -> SNS heartbeat
```

## Environment Configuration

Configuration is split between `cdk.json` (non-sensitive, committed) and SSM / `.env` (personal, never committed).

| Variable | Where | Used for |
|---|---|---|
| `github_repo`, `github_branch` | `cdk.json` context | Pipeline source |
| `github_owner` | SSM `/orders/pipeline/github_owner` | Pipeline source |
| `codestar_connection_arn` | SSM `/orders/pipeline/codestar_connection_arn` | GitHub connection |
| `alert_emails` | SSM `/orders/pipeline/alert_emails` | SNS subscriptions |
| `AWS_REGION`, `APP_NAME`, etc. | `.env` (optional, has defaults) | Local overrides |

### dev vs prod behavior

Controlled by `STAGE=dev` or `STAGE=prod` in your `.env`. The pipeline deploys both stages automatically.

| | dev | prod |
|---|---|---|
| VPC subnets | Public only | Public + private isolated |
| ECS task placement | Public subnet, public IP | Private subnet, no public IP |
| VPC Endpoints | None | ECR, ECR Docker, Secrets Manager, CloudWatch Logs, Kinesis + S3, DynamoDB |
| NACLs | Public only | Public + private |

## Implementation Status

- ✅ **Networking** — VPC multi-AZ, NACLs, prod/dev conditional (private subnets + VPC Endpoints in prod)
- ✅ **Storage** — DynamoDB PAY_PER_REQUEST + S3 for Firehose archive
- ✅ **Streaming** — KDS (ON_DEMAND, 24h retention) + Firehose -> S3 with date partitioning
- ✅ **Compute** — ECS Fargate + ALB + FastAPI admin panel + Secrets Manager API key
- ✅ **Processing** — Lambda processor (KDS -> DynamoDB), SQS DLQ via `on_failure` on event source mapping, X-Ray tracing
- ✅ **Observability** — 6 CloudWatch alarms, unified dashboard, log retention, SNS topic with email subscriptions
- ✅ **Incident Response** — EventBridge (ECS stopped, DLQ poll, heartbeat), DLQ re-driver Lambda
- ✅ **Pipeline** — Self-mutating CDK Pipelines CI/CD (dev -> prod with manual approval)

## AWS Domains Covered

| Domain | Coverage |
|---|---|
| D1 - SDLC | CDK Pipelines, self-mutating pipeline, multi-environment promotion, manual approval gate |
| D2 - Config Management | L2 constructs, cross-stack references, BundlingOptions, SSM Parameter Store |
| D3 - Resilient Solutions | Multi-AZ VPC, DynamoDB PAY_PER_REQUEST, KDS retention, SQS DLQ, bisect_batch_on_error |
| D4 - Monitoring | CloudWatch alarms, dashboard, log retention, X-Ray tracing |
| D5 - Incident Response | EventBridge event patterns, scheduled rules, auto-remediation Lambda |
| D6 - Security | Secrets Manager, IAM least privilege, VPC Endpoints, NACLs, non-root container |
