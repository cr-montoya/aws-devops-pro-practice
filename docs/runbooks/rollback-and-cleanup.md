# Runbook: Rollback and Cleanup

## SAM Cleanup

```bash
cd SAM
sam delete --config-env dev
sam delete --config-env prod
```

Dev and QA DynamoDB tables are deleted with the stack. Prod tables are retained by design.

Check retained tables:

```bash
aws dynamodb list-tables --region us-east-2
```

## CDK Cleanup

For direct deployments:

```bash
cd CDK
cdk destroy --all
```

For pipeline-managed environments, use the guarded teardown wave only when intentionally destroying the lab.

## Safety Checklist

- Confirm you are in the intended AWS account.
- Confirm the target region.
- Export or back up any data you need.
- Check retained DynamoDB tables and S3 buckets after stack deletion.
- Confirm alarms and SNS topics are removed if they are no longer needed.
