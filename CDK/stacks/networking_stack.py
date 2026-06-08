import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkingStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.is_production = stage == "prod"

        subnet_config = [
            ec2.SubnetConfiguration(
                name="public",
                subnet_type=ec2.SubnetType.PUBLIC,
                cidr_mask=24
            )
        ]

        if self.is_production:
            # PRIVATE_ISOLATED: no internet route — VPC endpoints provide AWS service access
            # Avoids NAT Gateway cost (~$32/month); VPC endpoints added when needed
            subnet_config.append(
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            )

        self.vpc = ec2.Vpc(self, "Vpc",
            vpc_name=f"{app_name}-{stage}-vpc",
            max_azs=2,
            subnet_configuration=subnet_config
        )

        self._add_public_nacl(app_name, stage)

        if self.is_production:
            self._add_private_nacl(app_name, stage)

    def _add_public_nacl(self, app_name: str, stage: str):
        nacl = ec2.NetworkAcl(self, "PublicNacl",
            vpc=self.vpc,
            network_acl_name=f"{app_name}-{stage}-public-nacl",
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        # Inbound: HTTP and HTTPS from internet (ALB listeners)
        nacl.add_entry("InboundHTTP",
            rule_number=100,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port(80),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )
        nacl.add_entry("InboundHTTPS",
            rule_number=110,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Inbound: ephemeral ports - return traffic from outbound connections (NACLs are stateless)
        nacl.add_entry("InboundEphemeral",
            rule_number=120,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )

        # Outbound: HTTPS to internet (ECR, Secrets Manager, Kinesis - dev only, prod uses VPC endpoints)
        nacl.add_entry("OutboundHTTPS",
            rule_number=100,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Outbound: ephemeral ports - return traffic to internet clients
        nacl.add_entry("OutboundEphemeral",
            rule_number=110,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )

    def _add_private_nacl(self, app_name: str, stage: str):
        # Private subnets only talk within the VPC (ALB -> ECS tasks, VPC endpoints)
        vpc_cidr = ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block)

        nacl = ec2.NetworkAcl(self, "PrivateNacl",
            vpc=self.vpc,
            network_acl_name=f"{app_name}-{stage}-private-nacl",
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # Inbound: container port from ALB (within VPC only)
        nacl.add_entry("InboundContainer",
            rule_number=100,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port(8080),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Inbound: ephemeral ports - return traffic from VPC endpoints (HTTPS responses)
        nacl.add_entry("InboundEphemeral",
            rule_number=110,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )

        # Outbound: HTTPS to VPC endpoints (ECR, Secrets Manager, Kinesis, CloudWatch)
        nacl.add_entry("OutboundHTTPS",
            rule_number=100,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Outbound: ephemeral ports - return traffic back to ALB
        nacl.add_entry("OutboundEphemeral",
            rule_number=110,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
