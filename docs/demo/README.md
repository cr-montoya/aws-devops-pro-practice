# Demo Evidence Guide

Use this folder to collect sanitized proof that the portfolio projects work.

Do not commit account IDs, secrets, API keys, private URLs, or sensitive logs.

## Suggested Evidence

## SAM

- `sam validate --lint` output
- `python -m pytest tests/unit -q` output
- `sam deploy --config-env dev` final output
- Smoke test results for:
  - `GET /health`
  - `POST /create_task`
  - `GET /tasks/{task_id}`
  - `GET /tasks?limit=1`
- Screenshot of CloudWatch alarms in `OK`
- Screenshot of Lambda aliases

## CDK

- `cdk synth` output
- CDK unit test output
- Screenshot of ECS service steady state
- Screenshot of ALB target group healthy
- Screenshot of CloudWatch dashboard
- DynamoDB item created after `POST /orders`
- DLQ depth at zero

## Naming

Suggested filenames:

```text
sam-deploy-dev.txt
sam-smoke-test.txt
cdk-synth.txt
cdk-tests.txt
ecs-service-steady-state.png
cloudwatch-dashboard.png
```
