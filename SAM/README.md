# Task API - Serverless Application

A simple serverless task management API built with AWS SAM, demonstrating best practices for DOP-C02 exam preparation.

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

## Commands

```bash
# Run all unit tests
python3 -m unittest discover tests/unit/ -v

# Build the application
sam build

# Deploy to AWS (first time uses --guided)
sam deploy --guided
sam deploy

# Test locally
sam local start-api  # http://localhost:3000

# Delete the stack
sam delete
```

## Testing in Postman

1. Import `swagger.json` into Postman
2. Get API Key:
   ```bash
   aws apigateway get-api-keys --include-values --region us-east-2
   ```
3. Add header: `x-api-key: <your-key>`
4. Test endpoints

## Key Features

- ✅ API Key authentication
- ✅ CORS enabled
- ✅ DynamoDB integration
- ✅ Unit tests with moto
- ✅ Separate Lambda per operation
- ✅ Least privilege IAM