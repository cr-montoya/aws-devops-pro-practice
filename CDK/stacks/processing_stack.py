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

        # SQS Dead Letter Queue for stream processing failures
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
        # Note: no dead_letter_queue here — that only applies to async invocations (SNS, S3, EventBridge).
        # For stream-based sources (KDS), the failure destination goes on the event source mapping.
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
        )

        # Event source: KDS -> Lambda
        # on_failure: after max_retry_attempts, the batch metadata is sent to the DLQ.
        # bisect_batch_on_error: splits a failing batch in half to isolate the bad record faster.
        event_source = lambda_event_sources.KinesisEventSource(
            stream=streaming_stack.stream,
            batch_size=10,
            starting_position=lambda_.StartingPosition.TRIM_HORIZON,
            bisect_batch_on_error=True,
            on_failure=lambda_event_sources.SqsDlq(dlq),
            retry_attempts=3,
        )
        self.processor.add_event_source(event_source)

        # SQS resource policy: restrict SendMessage to the Lambda service scoped to this function.
        # grant_consume_messages (used by the re-driver) adds identity-based policies on the IAM role,
        # but the on_failure delivery goes Lambda service -> SQS directly, so it needs a resource policy.
        dlq.add_to_resource_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
            actions=["sqs:SendMessage"],
            resources=[dlq.queue_arn],
            conditions={
                "ArnEquals": {"aws:SourceArn": self.processor.function_arn}
            }
        ))

        # Expose resources for downstream stacks
        self.dlq = dlq
        self.processor_role = lambda_role
