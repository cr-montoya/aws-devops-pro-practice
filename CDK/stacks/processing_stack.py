import aws_cdk as cdk
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_iam as iam
from aws_cdk import RemovalPolicy
from constructs import Construct


class ProcessingStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        streaming_stack: "StreamingStack",
        storage_stack: "StorageStack",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SQS Dead Letter Queue for failed messages
        dlq = sqs.Queue(self, "DLQ",
            queue_name=f"{app_name}-{stage}-dlq",
            retention_period=cdk.Duration.days(14),
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda execution role
        lambda_role = iam.Role(self, "ProcessorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # Grant permissions to Lambda role
        streaming_stack.stream.grant_read(lambda_role)
        storage_stack.table.grant_write_data(lambda_role)

        # Lambda function to process KDS events
        self.processor = lambda_.Function(self, "Processor",
            function_name=f"{app_name}-{stage}-processor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda", bundling=cdk.BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                command=[
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output && cp -r . /asset-output"
                ],
            )),
            handler="processor.handler",
            role=lambda_role,
            timeout=cdk.Duration.seconds(60),
            memory_size=256,
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "TABLE_NAME": storage_stack.table.table_name,
            },
            dead_letter_queue=dlq,
        )

        # Event source: KDS → Lambda with bisect on error
        event_source = lambda_event_sources.KinesisEventSource(
            stream=streaming_stack.stream,
            batch_size=10,
            starting_position=lambda_.StartingPosition.TRIM_HORIZON,
            bisect_batch_on_error=True,
        )
        self.processor.add_event_source(event_source)

        # Expose resources for downstream stacks
        self.dlq = dlq
        self.processor_role = lambda_role
