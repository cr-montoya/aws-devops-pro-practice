# AWS DevOps Professional Practice

![AWS](https://img.shields.io/badge/AWS-DevOps-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![AWS SAM](https://img.shields.io/badge/AWS-SAM-green)
![AWS CDK](https://img.shields.io/badge/AWS-CDK-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Hands-on AWS DevOps practice repository for the AWS Certified DevOps Engineer - Professional (DOP-C02) exam.

This repo contains two production-inspired AWS applications. Each app uses a small business domain so the infrastructure, deployment workflow, observability, and operational trade-offs are easy to inspect. The domains are examples, not the point: the same patterns can be adapted to many real workloads that need automated delivery, reliable rollback paths, environment-aware infrastructure, monitoring, and clear cleanup behavior.

## Projects

| Project | App domain | Main pattern | Focus area |
|---|---|---|---|
| [SAM Task API](SAM/README.md) | Task/status tracking API | Serverless REST API with safe Lambda deployments | SAM, API Gateway, Lambda aliases, CodeDeploy canaries, DynamoDB, CodePipeline |
| [CDK Orders Platform](CDK/README.md) | Event-driven order ingestion | Container API plus async stream processing | CDK, ECS Fargate, private networking, Kinesis, Lambda processors, incident response, CDK Pipelines |

## Repository Goals

- Practice DOP-C02 patterns through working infrastructure, not isolated snippets.
- Compare SAM and CDK as two different IaC workflows.
- Demonstrate dev-to-prod promotion with automated validation and manual approval.
- Model environment-specific behavior such as prod-only recovery and private workloads.
- Keep the app domains simple enough that the DevOps decisions remain visible.
- Preserve realistic operational concerns: IAM scope, observability, rollback, cost, and cleanup.
- Document architecture decisions and operational runbooks alongside the implementation.

## Architecture Overview

```text
aws-devops-pro-practice/
|
|-- SAM/
|   `-- Task API
|       |-- API Gateway REST API
|       |-- Lambda functions per operation
|       |-- DynamoDB task table
|       |-- CloudWatch alarms and access logs
|       `-- CodePipeline + CodeBuild + CloudFormation deploys
|
`-- CDK/
    `-- Orders Platform
        |-- ECS Fargate FastAPI service behind an ALB
        |-- Kinesis Data Streams and Firehose
        |-- Lambda stream processor and SQS DLQ
        |-- DynamoDB processed state and S3 raw archive
        |-- CloudWatch, SNS, EventBridge incident response
        `-- Self-mutating CDK Pipeline
```

## Reusable Patterns

The projects use concrete app domains, but the surrounding platforms are reusable.

The SAM app models a task API. The same pattern fits ticket intake, approval requests, inventory adjustments, status tracking, back-office workflows, or internal automation endpoints. The reusable pieces are API Gateway throttling, per-operation Lambda functions, DynamoDB state, canary Lambda deployments, alarm-based rollback, and a compact dev-to-prod pipeline.

The CDK app models order ingestion. The same pattern fits payments, inventory updates, IoT telemetry, audit logs, user activity streams, or background job intake. The reusable pieces are a containerized API, asynchronous stream processing, raw event archive, processed state store, DLQ recovery, private production networking, and incident automation.

## DOP-C02 Coverage

| Domain area | SAM Task API | CDK Orders Platform |
|---|---|---|
| SDLC automation | CodePipeline, CodeBuild, SAM package/deploy, manual prod approval | CDK Pipelines, synth, unit-test gate, self-mutation, manual prod approval |
| Configuration management and IaC | SAM/CloudFormation templates, parameters, stage behavior | CDK stacks, context, SSM lookups, stack composition |
| Resilient deployments | Lambda aliases, CodeDeploy canary traffic shifting, alarm rollback | Pipeline stages, ECS deployment behavior, guarded teardown wave |
| Monitoring and logging | Lambda alarms, API Gateway 5XX/latency alarms, access logs, X-Ray | CloudWatch alarms, dashboards, log retention, X-Ray, SNS notifications |
| Incident response | Alarm visibility around API and Lambda health | EventBridge incident rules, DLQ redriver schedule, SNS alerts |
| Security and compliance | API keys, usage plans, scoped deploy role, DynamoDB encryption | Secrets Manager, private prod tasks, VPC endpoints, IAM boundaries, non-root container |

## When To Use Each Project

Use `SAM/` when you want to focus on serverless delivery: Lambda versions, aliases, CodeDeploy canaries, REST API behavior, DynamoDB access, SAM packaging, and a compact CodePipeline.

Use `CDK/` when you want to focus on broader platform engineering: multi-stack IaC, ECS/Fargate operations, private networking, event streams, DLQs, incident automation, and CDK Pipelines.

Use both when you want to compare how the same DevOps ideas show up across different AWS deployment models.

## How To Review This Repo

1. Start with this README for the big picture and project comparison.
2. Open [SAM/README.md](SAM/README.md) if you want to inspect serverless delivery, Lambda canaries, API Gateway, DynamoDB, and SAM packaging.
3. Open [CDK/README.md](CDK/README.md) if you want to inspect platform engineering, ECS/Fargate, Kinesis, private networking, DLQs, and CDK Pipelines.
4. Review [docs/architecture](docs/architecture/) for diagrams.
5. Review [docs/adr](docs/adr/) to see why the main design choices were made.
6. Review [docs/runbooks](docs/runbooks/) to see how deployment failures and cleanup are handled.

## Repository Structure

```text
.
|-- README.md                         # Repo entry point and shared guidance
|-- Makefile                          # Common validation and build commands
|-- LICENSE                           # Project license
|-- CONTRIBUTING.md                   # Local contribution and validation notes
|-- SECURITY.md                       # Security reporting and lab-safety notes
|-- docs/
|   |-- architecture/                 # Mermaid diagrams
|   |-- adr/                          # Architecture decision records
|   |-- runbooks/                     # Operational troubleshooting notes
|   |-- costs.md
|   `-- dop-c02-mapping.md
|-- SAM/
|   |-- README.md                     # SAM Task API guide
|   |-- template.yaml                 # Serverless application template
|   |-- pipeline.yaml                 # CodePipeline for SAM app
|   |-- buildspec.yml                 # CodeBuild validation/build/package steps
|   |-- src/                          # Lambda handlers
|   `-- tests/                        # SAM unit tests
`-- CDK/
    |-- README.md                     # CDK Orders Platform guide
    |-- app.py                        # CDK app entry point
    |-- stacks/                       # CDK stacks
    |-- ecs/                          # FastAPI container app
    |-- lambda/                       # Stream processor and redriver
    `-- tests/                        # CDK unit tests
```

## Prerequisites

- AWS account with permission to create the resources used by each app
- AWS CLI configured for your target account
- Python 3.12+
- Git
- AWS SAM CLI for `SAM/`
- AWS CDK CLI and Docker for `CDK/`

The examples in this repo use `us-east-2`. You can adapt the region, but keep resource names and service availability in mind.

## Quick Start

Clone the repo:

```bash
git clone https://github.com/YOUR_USERNAME/aws-devops-pro-practice
cd aws-devops-pro-practice
```

Validate the SAM app:

```bash
cd SAM
python3 -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
python -m pytest tests/unit -q
sam validate --lint
sam build
```

Validate the CDK app:

```bash
cd ../CDK
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider
cdk synth
```

Each project README contains deployment-specific instructions.

## Common Commands

The root `Makefile` wraps the most common local checks:

```bash
make test-sam
make validate-sam
make build-sam
make test-cdk
make synth-cdk
make validate-all
```

## Documentation

Additional documentation lives in [docs/](docs/):

- [Architecture diagrams](docs/architecture/)
- [Architecture decision records](docs/adr/)
- [Runbooks](docs/runbooks/)
- [Cost guide](docs/costs.md)
- [DOP-C02 mapping](docs/dop-c02-mapping.md)

## Cost Notes

These are lab projects, but they create billable AWS resources.

Cost-aware design choices include:

- DynamoDB `PAY_PER_REQUEST` for both projects
- Prod-only recovery features where appropriate
- No NAT Gateway in the CDK production networking design
- Small compute defaults for lab use
- Explicit cleanup instructions in each app README

Resources to watch:

- API Gateway, Lambda, DynamoDB, CloudWatch, CodePipeline, CodeBuild, and S3 artifacts in `SAM/`
- ALB, Fargate, Kinesis, Firehose, VPC endpoints, Lambda, DynamoDB, S3, CloudWatch, CodePipeline, and CodeBuild in `CDK/`

Deploy only what you are actively validating and clean up afterward.

## Safety Notes

These projects are built for learning and experimentation. Before using either design in production, review account boundaries, IAM scope, encryption requirements, backup policy, secret rotation, WAF/TLS posture, deployment alarms, and organizational tagging standards.

The CDK project includes a guarded teardown workflow. The SAM project retains DynamoDB tables by default. Read the cleanup sections before deleting stacks.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
