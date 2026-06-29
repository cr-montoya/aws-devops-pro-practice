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
            # Avoids NAT Gateway cost (~$32/month)
            subnet_config.append(
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            )

        # Both DNS flags are required for VPC endpoint private DNS to override public resolution
        self.vpc = ec2.Vpc(self, "Vpc",
            vpc_name=f"{app_name}-{stage}-vpc",
            max_azs=2,
            subnet_configuration=subnet_config,
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        self._add_public_nacl(app_name, stage)

        if self.is_production:
            self._add_private_nacl(app_name, stage)
            self._add_vpc_endpoints(app_name, stage)

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
        # Inbound: ephemeral ports — return traffic from outbound connections (NACLs are stateless)
        nacl.add_entry("InboundEphemeral",
            rule_number=120,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )

        # Outbound: HTTPS to internet (dev tasks reach ECR/AWS directly; prod uses VPC endpoints)
        nacl.add_entry("OutboundHTTPS",
            rule_number=100,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Outbound: ALB health checks and requests to ECS tasks in private subnets
        nacl.add_entry("OutboundContainer",
            rule_number=105,
            cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
            traffic=ec2.AclTraffic.tcp_port(8080),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Outbound: ephemeral ports — return traffic to internet clients
        nacl.add_entry("OutboundEphemeral",
            rule_number=110,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )

    def _add_private_nacl(self, app_name: str, stage: str):
        # Private subnets only talk within the VPC (ALB -> tasks, tasks -> VPC endpoints)
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
        # Inbound: HTTPS — tasks and endpoint ENIs share this NACL; cross-AZ connections
        # require explicit 443 inbound on the receiving subnet (NACLs are stateless)
        nacl.add_entry("InboundHTTPS",
            rule_number=105,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Inbound: ephemeral ports — return traffic from interface endpoints and
        # gateway endpoints (S3/DynamoDB use public service IPs routed via VPCE)
        nacl.add_entry("InboundEphemeral",
            rule_number=110,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW
        )

        # Outbound: HTTPS to interface and gateway endpoints.
        # S3/DynamoDB gateway endpoints still use public service IP ranges, but the
        # isolated subnet route table has no default route to the internet.
        nacl.add_entry("OutboundHTTPS",
            rule_number=100,
            cidr=ec2.AclCidr.any_ipv4(),
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )
        # Outbound: ephemeral ports — return traffic to ALB
        nacl.add_entry("OutboundEphemeral",
            rule_number=110,
            cidr=vpc_cidr,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW
        )

    def _add_vpc_endpoints(self, app_name: str, stage: str):
        private_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)

        # Shared SG for all interface endpoints. allow_all_outbound=True is required —
        # restricting egress causes ENI_SG_RULES_MISMATCH and breaks endpoint functionality.
        # Exposed as self.endpoints_sg so ComputeStack can add the task SG as ingress.
        self.endpoints_sg = ec2.SecurityGroup(self, "EndpointsSG",
            vpc=self.vpc,
            security_group_name=f"{app_name}-{stage}-endpoints-sg",
            description="Allow HTTPS from within VPC to interface endpoints",
            allow_all_outbound=True
        )
        self.endpoints_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="HTTPS from VPC CIDR"
        )

        # Interface endpoints — PrivateLink, billed per AZ per hour (~$7/month each)
        # Required for Fargate in PRIVATE_ISOLATED subnets (no internet route):
        # - ECR API + Docker: image pull authentication and layer download
        # - ECS + ECS Agent + ECS Telemetry: task registration, heartbeat, container insights
        # - STS: IAM task role credential refresh
        # - Secrets Manager, CloudWatch Logs, Kinesis: application-level access
        for endpoint_id, service in [
            ("EcrApiEndpoint", ec2.InterfaceVpcEndpointAwsService.ECR),
            ("EcrDockerEndpoint", ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER),
            ("EcsEndpoint", ec2.InterfaceVpcEndpointAwsService.ECS),
            ("EcsAgentEndpoint", ec2.InterfaceVpcEndpointAwsService.ECS_AGENT),
            ("EcsTelemetryEndpoint", ec2.InterfaceVpcEndpointAwsService.ECS_TELEMETRY),
            ("StsEndpoint", ec2.InterfaceVpcEndpointAwsService.STS),
            ("SecretsManagerEndpoint", ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER),
            ("CloudWatchLogsEndpoint", ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS),
            ("KinesisEndpoint", ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS),
        ]:
            ec2.InterfaceVpcEndpoint(self, endpoint_id,
                vpc=self.vpc,
                service=service,
                subnets=private_subnets,
                security_groups=[self.endpoints_sg],
                private_dns_enabled=True
            )

        # Gateway endpoints — free, no security group needed
        self.vpc.add_gateway_endpoint("S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        self.vpc.add_gateway_endpoint("DynamoDbEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
