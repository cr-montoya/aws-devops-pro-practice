# ADR 0001: Use SAM for the Task API

## Status

Accepted

## Context

The Task API is a small serverless workload with API Gateway, Lambda, DynamoDB, alarms, and safe Lambda deployments.

## Decision

Use AWS SAM instead of raw CloudFormation or CDK.

## Consequences

- SAM keeps the serverless template concise.
- `AutoPublishAlias` and `DeploymentPreference` make Lambda canary deployments easy to inspect.
- The project stays focused on serverless delivery rather than broader platform composition.
- Some generated resources require SAM-specific lint configuration and operational understanding.
