import aws_cdk as cdk
from constructs import Construct
from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.streaming_stack import StreamingStack
from stacks.processing_stack import ProcessingStack
from stacks.compute_stack import ComputeStack
from stacks.observability_stack import ObservabilityStack
from stacks.incident_response_stack import IncidentResponseStack


class AppStage(cdk.Stage):
    """
    Groups all application stacks into a single deployable unit for CDK Pipelines.
    CDK Pipelines requires a Stage subclass — it creates a separate CloudFormation
    execution scope and allows deploying the full app to dev and prod independently.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        component: str,
        alert_emails: list,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        networking = NetworkingStack(
            self, "Networking",
            app_name=app_name,
            stage=stage,
            description="VPC with public/private isolated subnets and VPC Endpoints",
        )

        storage = StorageStack(
            self, "Storage",
            app_name=app_name,
            stage=stage,
            component=component,
            description="DynamoDB table and S3 bucket for Kinesis Firehose archive",
        )

        streaming = StreamingStack(
            self, "Streaming",
            app_name=app_name,
            stage=stage,
            storage_stack=storage,
            description="Kinesis Data Streams and Firehose for real-time event processing",
        )

        processing = ProcessingStack(
            self, "Processing",
            app_name=app_name,
            stage=stage,
            streaming_stack=streaming,
            storage_stack=storage,
            description="Lambda stream processor (KDS -> DynamoDB) with SQS DLQ and X-Ray tracing",
        )

        compute = ComputeStack(
            self, "Compute",
            app_name=app_name,
            stage=stage,
            networking_stack=networking,
            storage_stack=storage,
            streaming_stack=streaming,
            description="ECS Fargate service with FastAPI and ALB",
        )

        observability = ObservabilityStack(
            self, "Observability",
            app_name=app_name,
            stage=stage,
            processing_stack=processing,
            streaming_stack=streaming,
            storage_stack=storage,
            compute_stack=compute,
            alert_emails=alert_emails,
            description="CloudWatch alarms, dashboard, log retention",
        )

        incident_response = IncidentResponseStack(
            self, "IncidentResponse",
            app_name=app_name,
            stage=stage,
            processing_stack=processing,
            observability_stack=observability,
            compute_stack=compute,
            description="EventBridge rules, SNS alerts, and DLQ auto-remediation Lambda",
        )

        # Explicit dependencies — enforce CloudFormation deployment order within the stage
        streaming.add_dependency(storage)
        processing.add_dependency(streaming)
        compute.add_dependency(networking)
        compute.add_dependency(storage)
        compute.add_dependency(streaming)
        observability.add_dependency(processing)
        observability.add_dependency(compute)
        incident_response.add_dependency(observability)
