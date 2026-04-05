import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class NetworkingStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, app_name: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "Vpc",
            vpc_name=f"{app_name}-{stage}-vpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )