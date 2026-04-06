import aws_cdk as cdk
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

        # Secrets Manager for API key
        self.secret = secretsmanager.Secret(self, "ApiKeySecret",
            secret_name=f"{app_name}-{stage}-api-key",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECS Cluster
        self.cluster = ecs.Cluster(self, "Cluster",
            vpc=networking_stack.vpc,
            cluster_name=f"{app_name}-{stage}-cluster",
            container_insights_v2=ecs.ContainerInsights.ENHANCED
        )

        # Task role with permissions
        task_role = iam.Role(self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Grant permissions to task role
        streaming_stack.stream.grant_write(task_role)
        storage_stack.table.grant_read_data(task_role)
        storage_stack.table.grant_write_data(task_role)
        self.secret.grant_read(task_role)

        # ALB Fargate Service with FastAPI container
        self.service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=self.cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            service_name=f"{app_name}-{stage}-web-service",
            load_balancer_name=f"{app_name}-{stage}-alb",
            assign_public_ip=True,
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

        # Configure health check
        self.service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200"
        )

        # Expose ALB
        self.alb = self.service.load_balancer
