# Task API - Serverless Application

A simple serverless task management API built with AWS SAM, demonstrating best practices for DOP-C02 exam preparation.

**Author:** Cristian Montoya

## Table of Contents

- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Deployment](#deployment)
  - [Pipeline Architecture](#pipeline-architecture)
  - [Local Development](#local-development)
  - [Deploy Pipeline Stack](#deploy-pipeline-stack-one-time-setup)
  - [After Activation](#after-activation)
- [Testing Endpoints](#testing-endpoints)
  - [Get API Key](#get-api-key)
  - [Using Postman](#using-postman)
  - [Using cURL](#using-curl)
- [Key Features](#key-features)

## Project Structure

```
SAM/
├── src/
│   ├── health_check/        # Health check endpoint
│   ├── create_task/         # Create a new task
│   ├── get_task/            # Get a single task by ID
│   ├── list_task/           # List all tasks
│   └── update_task/         # Update task status
├── tests/
│   └── unit/                # Unit tests for all functions
├── template.yaml            # SAM template (infrastructure as code)
├── samconfig.toml           # SAM deployment configuration
└── swagger.json             # API documentation
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/create_task` | Create a new task |
| `GET` | `/tasks` | List all tasks |
| `GET` | `/tasks/{task_id}` | Get a single task |
| `PUT` | `/tasks/{task_id}` | Update task status |

**All endpoints require `x-api-key` header.**

## Prerequisites

- AWS credentials configured (`aws configure`)
- Python 3.12+
- AWS SAM CLI

## Setup

```bash
cd SAM
python3 -m venv venv
source venv/bin/activate
pip install -r tests/unit/requirements.txt
```

## Deployment

This application uses an automated CI/CD pipeline via AWS CodePipeline.

### Pipeline Architecture

```
GitHub (serverless branch)
  ↓
CodePipeline triggers automatically
  ↓
CodeBuild: install → run tests → sam build → sam package
  ↓
Deploy to Dev (automatic, Stage=dev)
  ↓
Manual Approval Gate (email notification)
  ↓
Deploy to Prod (Stage=prod, with canary deployment)
  ├→ 10% traffic to new version for 5 minutes
  ├→ CloudWatch Alarms monitor errors
  └→ Auto-rollback if errors detected
```

### Local Development

```bash
# Run all unit tests
python3 -m unittest discover tests/unit/ -v

# Build the application
sam build

# Deploy locally (without pipeline)
sam deploy --profile dev

# Test locally
sam local start-api  # http://localhost:3000

# Delete a stack
sam delete
```

### Deploy Pipeline Stack (One-time Setup)

```bash
aws cloudformation deploy \
  --template-file SAM/pipeline.yaml \
  --stack-name task-api-pipeline \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOwner=<your-github-username> \
    GitHubRepo=<repository-name> \
    GitHubBranch=serverless \
    ApprovalEmail=<your-email> \
  --region us-east-2
```

Then manually activate the GitHub connection in AWS Console:
1. Go to Developer Tools → Connections
2. Find `task-api-github-connection`
3. Click "Update pending connection" and authorize OAuth

### After Activation

Just push to the `serverless` branch—the pipeline triggers automatically:
- ✅ Tests run in CodeBuild
- ✅ Dev deploys automatically
- ✅ Prod requires manual approval
- ✅ Prod uses canary deployment (safer rollouts)

## Testing Endpoints

### Get API Key
```bash
aws apigateway get-api-keys --include-values --region us-east-2
```

### Using Postman
1. Import `swagger.json` into Postman
2. Set `x-api-key` header with your API key
3. Test endpoints

### Using cURL
```bash
curl -X POST https://<api-id>.execute-api.us-east-2.amazonaws.com/dev/create_task \
  -H "x-api-key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"task_name": "Example Task"}'
```

## Key Features

### Application
-  API Key authentication
-  CORS enabled
-  DynamoDB integration
-  Unit tests with moto
-  Separate Lambda per operation
-  Least privilege IAM

### CI/CD Pipeline
-  Automated deployments on push
-  Automatic unit testing via CodeBuild
-  Multi-environment (dev → prod)
-  Canary deployments in production (10% → 100%)
-  Automatic rollback on errors
-  CloudWatch Alarms monitoring per Lambda
-  Manual approval gate before prod