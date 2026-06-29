import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import RemovalPolicy
from constructs import Construct


class ComputeStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        networking_stack: "NetworkingStack",
        storage_stack: "StorageStack",
        streaming_stack: "StreamingStack",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # API key in Secrets Manager — task role has grant_read so the container
        # fetches it at startup without hardcoding credentials
        self.secret = secretsmanager.Secret(self, "ApiKeySecret",
            secret_name=f"{app_name}-{stage}-api-key",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ENHANCED container insights publishes CPU/memory/network metrics to CloudWatch
        self.cluster = ecs.Cluster(self, "Cluster",
            vpc=networking_stack.vpc,
            cluster_name=f"{app_name}-{stage}-cluster",
            container_insights_v2=ecs.ContainerInsights.ENHANCED
        )

        # Task role — identity assumed by the running container (not the ECS agent).
        # Least privilege: only the actions FastAPI needs at runtime.
        task_role = iam.Role(self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        streaming_stack.stream.grant_write(task_role)
        storage_stack.table.grant_read_data(task_role)
        storage_stack.table.grant_write_data(task_role)
        self.secret.grant_read(task_role)

        # dev: public subnets + public IP (direct internet access to ECR/AWS services)
        # prod: private isolated subnets + no public IP (VPC endpoints handle AWS traffic)
        task_subnets = (
            ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            if networking_stack.is_production
            else ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        # L3 pattern — provisions ECS service, task definition, ALB, target group and
        # listener in one construct. circuit_breaker rolls back instead of retrying for
        # up to 3 hours (default ECS behavior without it).
        self.service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=self.cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            service_name=f"{app_name}-{stage}-web-service",
            load_balancer_name=f"{app_name}-{stage}-alb",
            assign_public_ip=not networking_stack.is_production,
            task_subnets=task_subnets,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("ecs"),
                container_port=8080,
                task_role=task_role,
                environment={
                    "STREAM_NAME": f"{app_name}-{stage}-stream",
                    "SECRET_ARN": self.secret.secret_arn,
                    "AWS_DEFAULT_REGION": self.region
                }
            ),
            public_load_balancer=True,
            min_healthy_percent=100,
        )

        self.service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200"
        )

        # prod: add task SG as explicit ingress on the VPC endpoints SG.
        # CfnSecurityGroupIngress lives here (compute) to avoid a circular dependency —
        # compute already imports networking via VPC refs, so networking cannot import back.
        if networking_stack.is_production:
            task_sg = self.service.service.connections.security_groups[0]
            ec2.CfnSecurityGroupIngress(self, "EndpointSgTaskIngress",
                group_id=networking_stack.endpoints_sg.security_group_id,
                ip_protocol="tcp",
                from_port=443,
                to_port=443,
                source_security_group_id=task_sg.security_group_id,
                description="HTTPS from ECS tasks to VPC endpoints"
            )

        self.alb = self.service.load_balancer
