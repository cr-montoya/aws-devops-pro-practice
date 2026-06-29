# DOP-C02 Mapping

This repository is not a complete exam guide, but it gives hands-on coverage for recurring AWS DevOps Professional themes.

## SDLC Automation

- SAM CodePipeline with CodeBuild validation and CloudFormation deployments.
- CDK Pipeline with synth, tests, dev deployment, manual approval, and prod promotion.
- Build artifacts and packaged Lambda/container assets.

## Configuration Management and IaC

- SAM templates with parameters and stage-specific behavior.
- CDK multi-stack architecture with explicit dependencies.
- Environment-aware differences between dev and prod.

## Resilient Deployment Patterns

- Lambda aliases and canary deployments through CodeDeploy.
- Manual approval before production.
- ECS deployment guardrails and rollback-oriented pipeline design.

## Monitoring and Logging

- Lambda error alarms.
- API Gateway 5XX and latency alarms.
- ECS, Lambda, stream, DLQ, and dashboard monitoring.
- API access logs and bounded log retention.

## Incident and Event Response

- SNS notifications.
- EventBridge incident rules.
- Scheduled DLQ redriver automation.
- Runbooks for deploy failure and cleanup.

## Security and Compliance

- API keys and usage plans.
- Least-privilege-oriented deploy roles.
- Secrets Manager for application API key.
- Private production ECS tasks.
- VPC endpoints instead of NAT for AWS service access.
- DynamoDB encryption and prod-only recovery posture.
