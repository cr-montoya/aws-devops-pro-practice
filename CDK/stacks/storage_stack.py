import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import RemovalPolicy
from constructs import Construct

class StorageStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, app_name: str, stage: str, component: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.table = dynamodb.Table(self, "Table",
            table_name=f"{app_name}-{stage}-table",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False
        )

        self.bucket = s3.Bucket(self, "Bucket",
            bucket_name=f"{app_name}-{stage}-{component}-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )