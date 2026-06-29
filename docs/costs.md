# Cost Guide

This repository is designed for low-cost study, but both apps create billable resources.

## SAM Task API

| Service | Cost driver | Notes |
|---|---|---|
| API Gateway REST API | Requests | Low cost for light testing |
| Lambda | Invocations and duration | Small functions, low memory |
| DynamoDB | On-demand requests and storage | PAY_PER_REQUEST |
| CloudWatch | Logs, alarms, metrics | Alarms and API logs are the main steady cost |
| CodeBuild | Build minutes | Only during pipeline runs |
| CodePipeline | Active pipeline | Monthly active pipeline cost |
| S3 | Packaged artifacts | Small storage footprint |

## CDK Orders Platform

| Service | Cost driver | Notes |
|---|---|---|
| ALB | Hourly and LCU | One of the larger steady costs |
| ECS Fargate | vCPU/memory runtime | Stop/destroy when not studying |
| Kinesis Data Streams | Shard hours and PUT payload units | Keep shard count low |
| Firehose | Ingested data | Low for test payloads |
| S3 | Raw archive storage | Add lifecycle policy for long-lived labs |
| DynamoDB | On-demand requests and storage | PAY_PER_REQUEST |
| VPC endpoints | Interface endpoint hourly cost | Avoids NAT, but endpoints still cost money |
| CloudWatch | Logs, alarms, dashboards | Watch log retention |
| CodeBuild/CodePipeline | Pipeline runs and active pipeline | Destroy if not actively using |

## Cost Hygiene

- Prefer direct deploys for short experiments.
- Destroy stacks when done.
- Keep log retention bounded.
- Avoid leaving ECS/ALB/Kinesis running unnecessarily.
- Check retained DynamoDB tables and S3 buckets after cleanup.
