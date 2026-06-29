# Runbook: SAM Deploy Failure

## Symptoms

`sam deploy --config-env dev` fails during change set creation or stack creation.

Common messages:

- `AWS::EarlyValidation::ResourceExistenceCheck`
- `CloudWatch Logs role ARN must be set in account settings`
- Stack ends in `ROLLBACK_COMPLETE`

## Checks

```bash
aws cloudformation describe-stacks \
  --stack-name task-application-dev \
  --region us-east-2

aws cloudformation describe-stack-events \
  --stack-name task-application-dev \
  --region us-east-2 \
  --max-items 30
```

## Retained DynamoDB Table Conflict

If the error mentions resource existence, check for a retained table:

```bash
aws dynamodb describe-table \
  --table-name tasks-dev \
  --region us-east-2
```

For disposable dev data:

```bash
aws dynamodb delete-table --table-name tasks-dev --region us-east-2
aws dynamodb wait table-not-exists --table-name tasks-dev --region us-east-2
```

Then delete the failed stack and retry:

```bash
aws cloudformation delete-stack --stack-name task-application-dev --region us-east-2
aws cloudformation wait stack-delete-complete --stack-name task-application-dev --region us-east-2

cd SAM
rm -rf .aws-sam
sam build
sam deploy --config-env dev
```

## API Gateway CloudWatch Logs Role

If API Gateway stage creation fails because the CloudWatch Logs role is missing, ensure the template includes:

- `AWS::IAM::Role` for API Gateway CloudWatch logging
- `AWS::ApiGateway::Account`
- `DependsOn` from the API to the account setting

Then rebuild before deploying. A stale `.aws-sam/build/template.yaml` can cause SAM to deploy an older template.
