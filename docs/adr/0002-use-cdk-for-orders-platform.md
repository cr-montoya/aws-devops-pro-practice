# ADR 0002: Use CDK for the Orders Platform

## Status

Accepted

## Context

The Orders Platform combines networking, ECS, Kinesis, Lambda, DynamoDB, S3, observability, incident response, and a self-mutating pipeline.

## Decision

Use AWS CDK in Python.

## Consequences

- CDK makes multi-stack composition easier than maintaining large CloudFormation templates.
- Stack references model dependencies between networking, storage, streaming, compute, and observability.
- Unit tests can assert synthesized infrastructure.
- The project demonstrates a different IaC style than the SAM app.
