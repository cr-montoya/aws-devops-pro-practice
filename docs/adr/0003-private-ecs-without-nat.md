# ADR 0003: Run Production ECS Tasks Without NAT

## Status

Accepted

## Context

Production ECS tasks should avoid public IPs. NAT gateways add recurring cost and are not required if the service only needs AWS APIs.

## Decision

Place prod ECS tasks in private isolated subnets and use VPC endpoints for required AWS services.

## Consequences

- No public task IPs in prod.
- No NAT Gateway cost for this lab.
- ECR image pulls require ECR API, ECR Docker, and S3 access.
- Operational dependencies are explicit through endpoint and security group configuration.
