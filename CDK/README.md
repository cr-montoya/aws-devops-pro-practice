# Orders Platform - AWS CDK Event-Driven DevOps Project

Production-style AWS CDK project built as part of my AWS Certified DevOps Engineer - Professional (DOP-C02) study path and portfolio.

The application is intentionally small: a FastAPI service receives orders, publishes them to Kinesis, a Lambda processor persists them in DynamoDB, and the platform includes observability, incident response, and CI/CD automation. I modeled the domain around orders, but the same architecture fits any workload that needs to accept events quickly, process them asynchronously, retain raw records, and operate with production-style visibility. Examples include payments, inventory updates, IoT telemetry, audit events, user activity streams, or background job intake.

## What This Project Demonstrates

- Multi-stack AWS CDK app in Python
- ECS Fargate service behind an Application Load Balancer
- Private production workloads with no public task IPs
- ECR image pulls from isolated subnets using VPC endpoints instead of NAT
- Kinesis Data Streams and Firehose for event ingestion and raw archive
- Lambda stream processing with SQS DLQ failure handling
- DynamoDB on-demand table with PITR enabled only in prod
- CloudWatch alarms, dashboards, log retention, SNS notifications, and X-Ray
- EventBridge rules for incident detection and scheduled auto-remediation
- Self-mutating CDK Pipeline with unit-test gate, dev deployment, manual prod approval, and optional teardown guard

## Table of Contents

- [Architecture](#architecture)
- [How the Application Works](#how-the-application-works)
- [Project Structure](#project-structure)
- [Environment Behavior](#environment-behavior)
- [First-Time Setup](#first-time-setup)
- [Development Workflow](#development-workflow)
- [CI/CD Pipeline](#cicd-pipeline)
- [Testing](#testing)
- [Operational Validation](#operational-validation)
- [Next Steps for Production](#next-steps-for-production)
- [AWS DevOps Professional Domains](#aws-devops-professional-domains)
- [Cost Notes](#cost-notes)
- [Key Design Decisions](#key-design-decisions)
- [Cleanup](#cleanup)

## Architecture

```text
Internet
  |
  v
Application Load Balancer (public subnets)
  |
  v
ECS Fargate - FastAPI (public in dev, private isolated in prod)
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

CloudWatch
  +--> alarms, dashboard, log retention

SNS
  +--> alarm notifications and EventBridge incident alerts

EventBridge
  +--> ECS task stopped alert
  +--> DLQ redriver schedule
  +--> heartbeat schedule
```

## How the Application Works

The platform models a small order-processing system, but the pattern is not order-specific. It is a reusable event-ingestion design for applications that need to receive data through an API, decouple ingestion from processing, store a queryable state, keep a raw archive, and recover from failures without losing events. Orders are used here because they make the flow easy to understand.

1. A client sends an order to the FastAPI service running on ECS Fargate.
2. The public ALB receives the request and forwards it to the ECS task on port `8080`.
3. FastAPI validates the API key stored in Secrets Manager.
4. The service publishes the order event to Kinesis Data Streams.
5. A Lambda function consumes Kinesis batches, transforms the payload, and writes the processed order to DynamoDB.
6. Kinesis Firehose archives raw events to S3 for replay, audit, or analytics scenarios.
7. If Lambda cannot process a stream batch after retries, the failure metadata goes to SQS DLQ.
8. EventBridge runs a scheduled DLQ redriver Lambda that retries failed work.
9. CloudWatch collects logs and metrics, evaluates alarms, and exposes the dashboard.
10. SNS receives alarm and incident notifications for human review.

In `dev`, the ECS task is intentionally easier to reach and debug: it runs in public subnets with a public IP. In `prod`, the task moves to private isolated subnets with no public IP. It can still pull its image from ECR and call AWS services through VPC endpoints, which is the core networking pattern this project demonstrates.

The application has three practical validation paths:

- `GET /health` confirms the container and ALB target group are healthy.
- `POST /orders` confirms ECS can publish to Kinesis.
- DynamoDB records, Lambda logs, and DLQ depth confirm the asynchronous processing path is working.

For a different domain, only the payload and processor logic would need to change. The surrounding platform remains useful: ECS handles the API, Kinesis absorbs event bursts, Lambda processes asynchronously, DynamoDB stores the current state, S3 keeps raw history, CloudWatch observes the system, and EventBridge automates operational responses.

## Project Structure

```text
CDK/
|-- app.py                              # Entry point; instantiates app stacks and PipelineStack
|-- cdk.json                            # CDK configuration and pipeline context
|-- .env.example                        # Local environment template
|-- requirements.txt                    # Runtime dependencies
|-- requirements-dev.txt                # Test/development dependencies
|-- stacks/
|   |-- networking_stack.py             # VPC, subnets, NACLs, VPC endpoints
|   |-- storage_stack.py                # DynamoDB and S3 archive bucket
|   |-- streaming_stack.py              # Kinesis Data Streams and Firehose
|   |-- processing_stack.py             # Lambda processor and SQS DLQ
|   |-- compute_stack.py                # ECS Fargate, ALB, FastAPI, Secrets Manager
|   |-- observability_stack.py          # Alarms, dashboard, log retention, SNS
|   |-- incident_response_stack.py      # EventBridge rules and DLQ redriver
|   |-- app_stage.py                    # Groups app stacks for pipeline deployments
|   `-- pipeline_stack.py               # Self-mutating CDK Pipeline
|-- lambda/
|   |-- processor.py                    # Kinesis batch processor
|   |-- dlq_redriver.py                 # DLQ retry automation
|   `-- requirements.txt                # Lambda bundled dependencies
|-- ecs/
|   |-- app.py                          # FastAPI service
|   |-- Dockerfile                      # Non-root Python container
|   `-- requirements.txt                # FastAPI, Uvicorn, boto3
`-- tests/unit/
    |-- conftest.py                     # Shared CDK stack fixtures
    |-- test_networking_stack.py
    |-- test_storage_stack.py
    |-- test_streaming_stack.py
    |-- test_processing_stack.py
    |-- test_compute_stack.py
    |-- test_observability_stack.py
    `-- test_incident_response_stack.py
```

## Environment Behavior

Environment behavior is controlled by the `stage` value passed to each stack.

| Capability | dev/test | prod |
|---|---|---|
| VPC subnets | Public only | Public + private isolated |
| ECS task placement | Public subnet | Private isolated subnet |
| ECS public IP | Enabled | Disabled |
| NAT Gateway | Not used | Not used |
| VPC endpoints | Not created | Created for required AWS services |
| DynamoDB billing | PAY_PER_REQUEST | PAY_PER_REQUEST |
| DynamoDB PITR | Disabled | Enabled |
| Private NACL | Not created | Created |
| Deployment promotion | Automatic in pipeline dev stage | Manual approval in pipeline |

## First-Time Setup

### 1. Install Dependencies

```bash
git clone https://github.com/YOUR_USERNAME/aws-devops-pro-practice
cd aws-devops-pro-practice/CDK

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configure Local Environment

```bash
cp .env.example .env
```

Edit `.env` for your account/region and optional overrides.

Common values:

| Variable | Purpose |
|---|---|
| `AWS_REGION` | Default deployment region |
| `APP_NAME` | Resource naming prefix |
| `STAGE` | Local direct-deploy stage, usually `dev` or `prod` |
| `COMPONENT` | S3/archive component name |
| `ALERT_EMAILS` | SNS email subscriptions for direct stack deployments |

### 3. Bootstrap CDK

```bash
cdk bootstrap
```

Run this once per account/region.

## Development Workflow

```bash
# Activate virtual environment
source .venv/bin/activate

# Run unit tests
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider

# Synthesize CloudFormation
cdk synth

# Inspect changes
cdk diff
```

### Direct Stack Deployment

Useful for fast iteration:

```bash
cdk deploy Networking
cdk deploy Storage
cdk deploy Streaming
cdk deploy Processing
cdk deploy Compute
cdk deploy Observability
cdk deploy IncidentResponse
```

Or deploy everything:

```bash
cdk deploy --all --require-approval never
```

## CI/CD Pipeline

The project includes a self-mutating CDK Pipeline:

```text
GitHub branch
  |
  v
Synth
  |
  v
UnitTests
  |
  v
Deploy Dev
  |
  v
Manual Approval
  |
  v
Deploy Prod
  |
  v
Optional teardown wave (manual approval required)
```

### Pipeline Prerequisites

The pipeline reads account-specific values from SSM Parameter Store:

Before deploying the pipeline, update the `github_branch` value in `cdk.json`. The repository keeps it as `<BRANCH_NAME>` so each user can point the pipeline to their own branch without changing Python code.

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

Create a GitHub connection in AWS CodePipeline/CodeConnections, complete the OAuth flow, and wait until the connection status is `Available`.

### Bootstrap the Pipeline

```bash
cdk deploy Pipeline
```

After the first deployment, pushes to the configured branch in `cdk.json` trigger the pipeline.

### Teardown Guard

The pipeline includes a destructive teardown wave protected by manual approval. Do not approve `ConfirmTeardown` during normal deployments. It is intentionally present for lab cleanup and portfolio demonstration of guarded destructive automation.

## Testing

The unit test suite uses CDK assertions to validate synthesized CloudFormation without requiring AWS credentials.

Current coverage includes:

- VPC, subnet, endpoint, and NACL behavior
- ECS public/private placement and endpoint access
- DynamoDB billing and prod-only PITR
- Kinesis stream and Firehose delivery
- Lambda runtime, timeout, tracing, DLQ behavior, and IAM basics
- CloudWatch alarms and dashboard
- EventBridge incident response rules

Run:

```bash
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider
```

Latest local result:

```text
53 passed
```

## Operational Validation

Before considering the deployment complete, validate the running environment:

```text
1. ECS service reaches steady state
2. Fargate task pulls the image from ECR without NAT
3. Target group health check is healthy
4. /health returns 200 through the ALB
5. POST /orders writes to Kinesis
6. Lambda processes the event
7. DynamoDB receives the order item
8. DLQ remains empty
9. CloudWatch logs, alarms, and dashboard are present
10. EventBridge rules and SNS notifications are configured
```

## Next Steps for Production

This project is intentionally scoped as a portfolio and study project, but the architecture can be extended toward a more production-ready workload. The next improvements would focus on scaling, edge security, encryption posture, and operational guardrails.

### ECS Service Scaling

The ECS service currently runs with a small fixed desired count, which is appropriate for a lab. A production version should configure service auto scaling based on meaningful signals. CPU and memory target tracking are good starting points, but request count per target from the ALB is often a better application-level signal for HTTP services. For event-heavy workloads, custom metrics such as order ingestion rate, downstream latency, or queue/dead-letter depth can help scale before user-facing symptoms appear.

### HTTPS, Certificates, and TLS Policy

The ALB currently models the application flow, but a production-facing endpoint should use HTTPS with an ACM certificate. The listener should redirect HTTP to HTTPS and enforce a modern TLS security policy with a minimum of TLS 1.2. This protects traffic in transit and makes the platform closer to what would be expected for a public application endpoint.

### Route 53 and Domain Management

A custom domain should be added with Route 53 records pointing to the ALB. This makes the deployment easier to consume and allows certificate validation, DNS-based routing, and future traffic-management patterns such as weighted records or failover records.

### AWS WAF

AWS WAF should be attached to the ALB to protect the API from common web threats. A practical baseline would include AWS managed rule groups, IP reputation lists, rate-based rules, and explicit allow/deny rules if the app has known traffic sources. This adds a useful security layer before requests ever reach ECS.

### AWS Shield

For internet-facing workloads, AWS Shield Standard is automatically included and provides baseline DDoS protection. A higher-risk or business-critical production system could evaluate Shield Advanced for enhanced protections, cost protection, and deeper response support. For this project, documenting Shield Standard and designing the ALB/WAF layer correctly is the natural first step.

### Stronger Deployment Safety

The pipeline already includes tests and manual approval before prod. A production extension could add smoke tests after dev deploy, CloudWatch alarm checks before promotion, deployment alarms for ECS circuit breaker decisions, and automated rollback criteria. This would make the pipeline closer to a mature progressive delivery workflow.

### Secrets and Configuration Lifecycle

Secrets Manager is already used for the API key. A production version should define a rotation strategy, audit access through CloudTrail, and separate operational configuration from secrets. Depending on the application, AWS AppConfig or SSM Parameter Store could manage non-secret runtime configuration.

### Data Protection

DynamoDB PITR is enabled in prod, but additional production controls could include deletion protection, stricter removal policies, backup plans through AWS Backup, S3 lifecycle policies, S3 versioning, and bucket access logging. These settings were intentionally lighter here to keep the lab easy to clean up.

### Observability Enhancements

The project already includes alarms, logs, dashboarding, and X-Ray. The next step would be service-level indicators: availability, latency, error rate, successful orders processed, failed orders, DLQ age, and Kinesis consumer lag. These metrics would make the dashboard more operationally meaningful and provide better alarm thresholds.

### ECS Exec and Break-Glass Operations

For production troubleshooting, ECS Exec can be enabled with strict IAM controls and CloudTrail auditing. This gives operators a controlled emergency path into running containers without opening SSH or exposing instances.

### Container Supply Chain

A production pipeline should scan container images, pin base image versions intentionally, and define a patching process. ECR image scanning or an external scanner can catch vulnerabilities before deployment. Signing images and enforcing deployment policies would be a strong next step for supply-chain hardening.

## AWS DevOps Professional Domains

| Domain | Project Coverage |
|---|---|
| D1 - SDLC Automation | CDK Pipelines, self-mutation, Docker asset publishing, Lambda asset packaging, test gate, manual approval |
| D2 - Configuration Management and IaC | CDK L2/L3 constructs, stack dependencies, environment-aware infrastructure, SSM lookups |
| D3 - Resilient Cloud Solutions | Multi-AZ networking, Kinesis retention, Lambda batch retry behavior, SQS DLQ, DynamoDB PITR in prod |
| D4 - Monitoring and Logging | CloudWatch alarms, dashboard, logs retention, X-Ray tracing |
| D5 - Incident and Event Response | EventBridge incident rules, scheduled remediation, SNS notifications |
| D6 - Security and Compliance | IAM least privilege, Secrets Manager, private prod tasks, VPC endpoints, non-root container |

## Cost Notes

This is a portfolio/lab project and creates billable AWS resources.

Cost-aware choices:

- No NAT Gateway for prod ECS tasks
- DynamoDB `PAY_PER_REQUEST`
- Single desired ECS task by default
- Gateway endpoints for S3 and DynamoDB
- Removal policies tuned for lab cleanup

Billable resources to watch:

- ALB hourly cost
- Fargate task runtime
- Interface VPC endpoints per AZ
- Kinesis Data Streams and Firehose usage
- CloudWatch logs, alarms, and dashboard
- CodePipeline and CodeBuild usage

## Key Design Decisions

### Orders as the Sample Domain

The project uses orders because the workflow is easy to reason about: a request comes in, an event is published, a processor updates state, and failures can be retried. The architecture is not limited to orders. The same design can support payment events, inventory updates, audit logs, user activity tracking, IoT telemetry, or any application that needs durable asynchronous event processing. Keeping the business domain simple makes the infrastructure decisions easier to inspect.

### ECS Fargate for the API Layer

The API runs on ECS Fargate because it represents a long-running containerized service, not a short-lived function. This makes the project cover task definitions, container images, ALB target groups, health checks, task roles, and image publishing through CDK assets. For the DOP-C02 study goal, this is more valuable than making every component serverless, because ECS operations and deployment behavior are common exam and real-world topics.

### Kinesis Between the API and Processor

Kinesis decouples ingestion from processing. FastAPI can accept an order and return quickly while downstream processing happens asynchronously. This protects the API from processor latency, gives the system a replay window through stream retention, and exposes useful operational signals such as iterator age. Firehose adds a raw S3 archive without requiring custom archive code.

### DynamoDB for Processed State

DynamoDB is used for the processed order state because it is serverless, operationally simple, and a good fit for key-value access by order ID. `PAY_PER_REQUEST` avoids capacity planning in a lab or portfolio environment. PITR is enabled only in prod because recovery capability matters most for production data, while dev and test stay cheaper and easier to clean up.

### Private Production ECS Tasks Without NAT

In prod, ECS tasks run in `PRIVATE_ISOLATED` subnets with no public IP and no internet route. They still pull container images and call AWS services through VPC endpoints. This is intentional: it demonstrates private workload design, avoids NAT Gateway cost for this workload, and keeps AWS service traffic on private connectivity paths. ECR pulls need both ECR endpoints and S3 access because image layers are downloaded through S3-backed infrastructure.

The interface endpoints cover ECR API, ECR Docker, ECS, ECS Agent, ECS Telemetry, STS, Secrets Manager, CloudWatch Logs, and Kinesis. Gateway endpoints cover S3 and DynamoDB.

### Explicit NACLs for Learning and Verification

The project keeps custom NACLs to make subnet-level traffic rules visible. Security groups are still the primary stateful control, but NACLs force the design to account for stateless return traffic, ALB-to-task health checks, interface endpoint HTTPS, and gateway endpoint behavior. This is especially useful for studying why ECR in private subnets needs more than just the ECR endpoints.

### CDK Pipelines and Direct Deploys

The repo supports direct stack deploys for fast iteration and CDK Pipelines for the full dev-to-prod workflow. This lets the project be practical while developing and still demonstrate a production-style pipeline with synth, tests, asset publishing, dev deployment, manual approval, and prod promotion. Directly deployed stacks and pipeline-deployed stacks have different CloudFormation names, so both workflows can coexist during practice.

## Cleanup

For directly deployed stacks:

```bash
cdk destroy --all
```

For the pipeline-managed environment, use the guarded teardown wave only when intentionally destroying the lab. After approving teardown, the pipeline itself is destroyed and must be bootstrapped again with:

```bash
cdk deploy Pipeline
```

## Portfolio Summary

This project demonstrates a production-inspired AWS DevOps workflow using CDK: infrastructure as code, containerized workloads, event-driven processing, private networking, observability, incident response automation, and self-mutating CI/CD. It is designed to show both hands-on implementation and the reasoning behind AWS DevOps Professional architecture decisions.
