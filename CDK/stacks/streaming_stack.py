import aws_cdk as cdk
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kinesisfirehose as firehose
from aws_cdk import Duration
from aws_cdk import RemovalPolicy
from constructs import Construct


class StreamingStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        storage_stack: "StorageStack",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Kinesis Data Streams — ingestion buffer between FastAPI and the Lambda processor
        # ON_DEMAND: no shard management, AWS scales capacity automatically
        # 24h retention: Lambda can re-read records if it falls behind or needs to replay
        # MANAGED encryption: AWS-managed KMS key, no extra cost
        self.stream = kinesis.Stream(self, "Stream",
            stream_name=f"{app_name}-{stage}-stream",
            stream_mode=kinesis.StreamMode.ON_DEMAND,
            retention_period=Duration.hours(24),
            removal_policy=RemovalPolicy.DESTROY,
            encryption=kinesis.StreamEncryption.MANAGED
        )

        # IAM role for Firehose — needs read from KDS and write to S3
        firehose_role = iam.Role(self, "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com")
        )
        storage_stack.bucket.grant_read_write(firehose_role)
        self.stream.grant_read(firehose_role)

        # Kinesis Data Firehose — archives raw events to S3 in parallel with Lambda processing
        # KDS -> Firehose -> S3 is independent of the Lambda path; raw data is always preserved
        # even if the processor fails. Prefix partitions by date for cost-efficient Athena queries.
        self.firehose = firehose.DeliveryStream(self, "Firehose",
            delivery_stream_name=f"{app_name}-{stage}-firehose",
            source=firehose.KinesisStreamSource(self.stream),
            destination=firehose.S3Bucket(
                bucket=storage_stack.bucket,
                data_output_prefix="raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/",
                error_output_prefix="errors/year=!{timestamp:yyyy}/month=!{timestamp:MM}/!{firehose:error-output-type}",
            )
        )
