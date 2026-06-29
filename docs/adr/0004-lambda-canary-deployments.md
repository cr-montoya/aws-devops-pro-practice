# ADR 0004: Use Lambda Canary Deployments in SAM

## Status

Accepted

## Context

The SAM project is intended to demonstrate safe serverless delivery and rollback behavior.

## Decision

Use `AutoPublishAlias: live` with `DeploymentPreference: Canary10Percent5Minutes` for all Lambda functions.

## Consequences

- New versions receive a small traffic percentage before full promotion.
- CloudWatch alarms can trigger rollback.
- The pattern is easy to identify for DOP-C02 study.
- Canary deployment on trivial functions may be more operational overhead than a production team would choose, but it is useful for this lab.
