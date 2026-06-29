# SAM Task API Architecture

```mermaid
flowchart TD
    Client[Client] --> APIGW[API Gateway REST API]
    APIGW --> UsagePlan[API key + usage plan]
    APIGW --> Health[HealthCheckFunction]
    APIGW --> Create[CreateTaskFunction]
    APIGW --> List[ListTasksFunction]
    APIGW --> Get[GetTaskFunction]
    APIGW --> Update[UpdateTaskFunction]

    Create --> DDB[(DynamoDB tasks table)]
    List --> DDB
    Get --> DDB
    Update --> DDB

    APIGW --> Logs[API Gateway access logs]
    Health --> LambdaAlarms[Lambda error alarms]
    Create --> LambdaAlarms
    List --> LambdaAlarms
    Get --> LambdaAlarms
    Update --> LambdaAlarms
    APIGW --> ApiAlarms[API 5XX and latency alarms]

    CodePipeline[CodePipeline] --> CodeBuild[CodeBuild]
    CodeBuild --> Validate[sam validate + unit tests]
    Validate --> Package[sam build + package]
    Package --> Dev[Deploy dev]
    Dev --> Approval[Manual approval]
    Approval --> Prod[Deploy prod]

    Prod --> CodeDeploy[CodeDeploy Lambda canary]
    CodeDeploy --> Alias[Lambda live aliases]
    LambdaAlarms --> Rollback[Alarm-based rollback]
```

## Key Flow

1. Clients call API Gateway with an API key.
2. API Gateway routes each operation to a dedicated Lambda function.
3. Lambda functions read/write the DynamoDB task table.
4. SAM publishes function versions behind `live` aliases.
5. CodeDeploy shifts traffic with `Canary10Percent5Minutes`.
6. CloudWatch alarms provide deployment rollback signals.
