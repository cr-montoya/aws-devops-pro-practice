# SAM Task API

Serverless task-management API built with AWS SAM. The root [README](../README.md) explains the repo goals, DOP-C02 coverage, shared cost notes, and how this project compares with the CDK app.

This app focuses on a compact serverless release pattern: API Gateway, Lambda, DynamoDB, CloudWatch alarms, Lambda canary deployments, and a dev-to-prod CodePipeline.

## Architecture

```text
Client
  |
  v
API Gateway REST API
  |-- API key required
  |-- Usage plan quota and throttling
  |-- CORS, access logs, X-Ray tracing
  |
  +--> GET  /health           --> HealthCheckFunction
  +--> POST /create_task      --> CreateTaskFunction
  +--> GET  /tasks            --> ListTasksFunction
  +--> GET  /tasks/{task_id}  --> GetTaskFunction
  +--> PUT  /tasks/{task_id}  --> UpdateTaskFunction
                                |
                                v
                             DynamoDB

CloudWatch alarms monitor Lambda errors, API Gateway 5XXs, and API latency.
SAM configures Lambda aliases and CodeDeploy canaries with Canary10Percent5Minutes.
```

## What Is Included

- `template.yaml`: SAM application template.
- `pipeline.yaml`: CodePipeline, CodeBuild, deploy role, and manual approval.
- `buildspec.yml`: installs test deps, runs `sam validate --lint`, unit tests, build, and package.
- `samconfig.toml`: direct deploy profiles for `dev` and `prod`.
- `src/`: Lambda handlers plus shared HTTP helpers.
- `tests/unit/`: moto-backed unit tests.
- `swagger.json`: portable API contract.
- `events/`: local invocation payloads.

## API

All endpoints require `x-api-key`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/create_task` | Create a task |
| `GET` | `/tasks?limit=25&next_token=<token>` | List tasks with pagination |
| `GET` | `/tasks/{task_id}` | Get one task |
| `PUT` | `/tasks/{task_id}` | Update task status |

Create:

```bash
curl -X POST "$API_URL/create_task" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Example Task"}'
```

Update:

```bash
curl -X PUT "$API_URL/tasks/<task-id>" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "DONE"}'
```

Allowed statuses: `PENDING`, `IN_PROGRESS`, `DONE`.

## Environment Behavior

| Capability | dev/qa | prod |
|---|---|---|
| DynamoDB PITR | Disabled | Enabled |
| DynamoDB deletion protection | Disabled | Enabled |
| API access log retention | 14 days | 90 days |
| Lambda tracing | Active | Active |
| Lambda deployment | Canary10Percent5Minutes | Canary10Percent5Minutes |
| Pipeline promotion | Automatic dev deploy | Manual approval before prod |

`AllowedCorsOrigin` defaults to `*` for lab convenience. Override it for production-style deployments.

## Local Workflow

```bash
cd SAM
python3 -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt

python -m pytest tests/unit -q
python3 -m unittest discover tests/unit/ -v
sam validate --lint
sam build
```

Local invokes:

```bash
sam local invoke HealthCheckFunction -e events/health_check.json
sam local invoke CreateTaskFunction -e events/create_task.json
sam local invoke ListTasksFunction -e events/list_tasks.json
```

Local API:

```bash
sam local start-api
curl "http://localhost:3000/health" -H "x-api-key: test-key"
```

## Direct Deploy

```bash
sam deploy --config-env dev
sam deploy --config-env prod
```

With restricted CORS:

```bash
sam deploy --config-env prod \
  --parameter-overrides Stage=prod AllowedCorsOrigin=https://example.com
```

## Pipeline

```text
Source -> Build -> DeployDev -> Manual Approval -> DeployProd
```

Build runs `sam validate --lint`, unit tests, `sam build`, and `sam package`. Lambda deployment safety is handled in the SAM template through aliases, CodeDeploy canary traffic shifting, and CloudWatch alarms.

Deploy the pipeline stack:

```bash
aws cloudformation deploy \
  --template-file pipeline.yaml \
  --stack-name task-api-pipeline \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOwner=<your-github-username> \
    GitHubRepo=<repository-name> \
    GitHubBranch=main \
    ApprovalEmail=<your-email> \
  --region us-east-2
```

After deployment, activate `task-api-github-connection` in AWS Developer Tools / Connections.

## Deployed Validation

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name task-application-dev \
  --query "Stacks[0].Outputs[?OutputKey=='TaskApiUrl'].OutputValue" \
  --output text \
  --region us-east-2)

aws apigateway get-api-keys --include-values --region us-east-2

curl "$API_URL/health" -H "x-api-key: $API_KEY"
curl "$API_URL/tasks?limit=1" -H "x-api-key: $API_KEY"
```

Check CloudWatch alarms, API access logs, DynamoDB items, and Lambda aliases after deployment.

## Troubleshooting

If `sam deploy --config-env dev` fails with `AWS::EarlyValidation::ResourceExistenceCheck`, check whether a retained table already exists:

```bash
aws dynamodb describe-table \
  --table-name tasks-dev \
  --region us-east-2
```

For disposable dev data, delete the retained table and retry the deploy:

```bash
aws dynamodb delete-table \
  --table-name tasks-dev \
  --region us-east-2

aws dynamodb wait table-not-exists \
  --table-name tasks-dev \
  --region us-east-2
```

For data you need to keep, import the table into CloudFormation or deploy with another `Stage` value. The template retains DynamoDB tables only in prod; dev and qa tables are deleted with the stack.

## Cleanup

```bash
sam delete --config-env dev
sam delete --config-env prod

aws cloudformation delete-stack \
  --stack-name task-api-pipeline \
  --region us-east-2
```

Prod DynamoDB tables are retained by design. Review retained `tasks-prod` tables after deleting prod stacks.
