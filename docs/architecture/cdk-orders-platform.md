# CDK Orders Platform Architecture

```mermaid
flowchart TD
    Client[Client] --> ALB[Application Load Balancer]
    ALB --> ECS[ECS Fargate FastAPI service]
    ECS --> KDS[Kinesis Data Streams]
    ECS --> Secrets[Secrets Manager API key]

    KDS --> Processor[Lambda stream processor]
    KDS --> Firehose[Kinesis Firehose]
    Firehose --> Archive[(S3 raw archive)]
    Processor --> Orders[(DynamoDB processed orders)]
    Processor --> DLQ[SQS DLQ]

    EventBridge[EventBridge] --> Redriver[DLQ redriver Lambda]
    Redriver --> DLQ
    Redriver --> Processor

    ECS --> Logs[CloudWatch Logs]
    Processor --> Logs
    DLQ --> Alarms[CloudWatch alarms and dashboard]
    KDS --> Alarms
    ALB --> Alarms
    Alarms --> SNS[SNS notifications]

    subgraph ProdNetworking[Prod private networking]
        ECS
        VPCE[VPC endpoints for ECR, S3, DynamoDB, Logs, STS, Secrets, Kinesis]
    end
```

## Key Flow

1. ALB receives HTTP traffic and forwards it to ECS Fargate.
2. FastAPI validates the API key and publishes order events to Kinesis.
3. Lambda consumes stream records and writes processed state to DynamoDB.
4. Firehose archives raw events to S3.
5. Failed stream batches are routed to SQS DLQ.
6. EventBridge triggers remediation and incident-response workflows.
