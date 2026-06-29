# Runbook: CDK Pipeline Failure

## Symptoms

CDK pipeline fails in synth, asset publishing, test, or deployment stages.

## Triage

1. Identify the failing CodeBuild project or CloudFormation stack.
2. Read the CodeBuild phase logs.
3. Check whether failure happened before or after `cdk synth`.
4. Inspect CloudFormation events for failed stack resources.

## Useful Commands

```bash
cd CDK
cdk synth
cdk diff
.venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider
```

For stack events:

```bash
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --region us-east-2 \
  --max-items 30
```

## Common Causes

- Missing SSM parameters for pipeline configuration.
- CodeStar/CodeConnections connection not activated.
- Docker asset build failures.
- VPC endpoint or security group changes blocking ECS image pulls.
- IAM policy changes not attached to the right CodeBuild step.

## Recovery

Fix the source issue, rerun local synth/tests, then push a new commit. For direct stack deployments, use `cdk deploy <StackName>` after confirming `cdk diff`.
