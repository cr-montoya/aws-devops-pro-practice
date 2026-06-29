# CDK Orders Platform

Event-driven orders platform built with AWS CDK. The root [README](../README.md) explains the repo goals, DOP-C02 coverage, shared cost notes, and how this project compares with the SAM app.

This app focuses on a broader platform pattern: ECS Fargate API, private production networking, Kinesis ingestion, Lambda processing, DLQ recovery, observability, incident response, and CDK Pipelines.

Related docs:

- [Architecture diagram](../docs/architecture/cdk-orders-platform.md)
- [Pipeline diagram](../docs/architecture/pipelines.md)
- [CDK pipeline runbook](../docs/runbooks/cdk-pipeline-failure.md)
- [Private ECS without NAT ADR](../docs/adr/0003-private-ecs-without-nat.md)

## Architecture

```text
Internet
  |
  v
Application Load Balancer
  |
  v
ECS Fargate - FastAPI
  |
  +--> POST /orders
          |
          v
       Kinesis Data Streams
          |
          +--> Lambda processor --> DynamoDB
          |         |
          |         +--> SQS DLQ on failed stream batches
          |
          +--> Kinesis Firehose --> S3 raw archive

CloudWatch: alarms, dashboard, logs, X-Ray
SNS: alarm and incident notifications
EventBridge: ECS incident alerts, DLQ redriver schedule, heartbeat schedule
```

## What Is Included

- `app.py`: CDK entry point.
- `stacks/`: networking, storage, streaming, processing, compute, observability, incident response, app stage, and pipeline stacks.
- `ecs/`: FastAPI container app and Dockerfile.
- `lambda/`: Kinesis processor and DLQ redriver.
- `tests/unit/`: CDK assertion tests.
- `cdk.json`: app and pipeline context.
- `.env.example`: local direct-deploy configuration template.

## Environment Behavior

| Capability | dev/test | prod |
|---|---|---|
| ECS task placement | Public subnet | Private isolated subnet |
| ECS public IP | Enabled | Disabled |
| NAT Gateway | Not used | Not used |
| VPC endpoints | Not created | Created for required AWS services |
| DynamoDB PITR | Disabled | Enabled |
| Private NACL | Not created | Created |
| Pipeline promotion | Automatic dev deploy | Manual approval before prod |

Prod tasks run without public IPs and use VPC endpoints for AWS service access, including ECR image pulls.

## Local Workflow

```bash
cd CDK
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider
cdk synth
cdk diff
```

Bootstrap once per account/region:

```bash
cdk bootstrap
```

## Direct Deploy

Deploy individual stacks while iterating:

```bash
cdk deploy Networking
cdk deploy Storage
cdk deploy Streaming
cdk deploy Processing
cdk deploy Compute
cdk deploy Observability
cdk deploy IncidentResponse
```

Or deploy all direct stacks:

```bash
cdk deploy --all --require-approval never
```

## Pipeline

```text
Synth -> UnitTests -> Deploy Dev -> Manual Approval -> Deploy Prod -> Optional teardown wave
```

Pipeline prerequisites are stored in SSM Parameter Store:

```bash
aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/github_owner" \
  --value "your-github-username" \
  --type "String"

aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/codestar_connection_arn" \
  --value "arn:aws:codeconnections:us-east-2:ACCOUNT_ID:connection/..." \
  --type "String"

aws ssm put-parameter --region us-east-2 \
  --name "/orders/pipeline/alert_emails" \
  --value "your@email.com" \
  --type "String"
```

Set `github_branch` in `cdk.json`, create/activate the GitHub CodeConnections connection, then deploy:

```bash
cdk deploy Pipeline
```

Do not approve `ConfirmTeardown` during normal deployments. It exists as a guarded cleanup demonstration.

## Validation

Unit tests:

```bash
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider
```

Current coverage validates synthesized infrastructure for networking, storage, streaming, processing, compute, observability, and incident response behavior.

After deployment, validate:

```text
1. ECS service reaches steady state
2. Target group health check is healthy
3. GET /health returns 200 through the ALB
4. POST /orders writes to Kinesis
5. Lambda processes the event
6. DynamoDB receives the order item
7. DLQ remains empty
8. CloudWatch alarms and dashboard exist
9. EventBridge rules and SNS notifications are configured
```

## Production Extensions

The project is intentionally scoped for practice. The natural production hardening path would add HTTPS/ACM, Route 53, AWS WAF, stronger smoke tests before promotion, container image scanning, secret rotation, backup plans, and service-level metrics.

## Cleanup

For directly deployed stacks:

```bash
cdk destroy --all
```

For pipeline-managed environments, use the guarded teardown wave only when intentionally destroying the lab. After approving teardown, the pipeline must be bootstrapped again with:

```bash
cdk deploy Pipeline
```
