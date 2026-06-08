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

        # API key stored in Secrets Manager — loaded by FastAPI at container startup
        # The task role has grant_read so the container fetches it without hardcoding credentials
        self.secret = secretsmanager.Secret(self, "ApiKeySecret",
            secret_name=f"{app_name}-{stage}-api-key",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ECS Cluster — ENHANCED container insights publishes CPU/memory/network metrics to CloudWatch
        self.cluster = ecs.Cluster(self, "Cluster",
            vpc=networking_stack.vpc,
            cluster_name=f"{app_name}-{stage}-cluster",
            container_insights_v2=ecs.ContainerInsights.ENHANCED
        )

        # Task role — identity assumed by the running container (not the ECS agent)
        # Follows least privilege: only the specific actions the FastAPI needs
        task_role = iam.Role(self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        streaming_stack.stream.grant_write(task_role)
        storage_stack.table.grant_read_data(task_role)
        storage_stack.table.grant_write_data(task_role)
        self.secret.grant_read(task_role)

        # dev: tasks in public subnets with public IP (reaches ECR/AWS services directly over internet)
        # prod: tasks in private isolated subnets, no public IP (VPC endpoints handle AWS service traffic)
        task_subnets = (
            ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
            if networking_stack.is_production
            else ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        # ApplicationLoadBalancedFargateService (L3 pattern):
        # provisions ECS service + task definition + ALB + target group + listener in one construct
        self.service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=self.cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            service_name=f"{app_name}-{stage}-web-service",
            load_balancer_name=f"{app_name}-{stage}-alb",
            assign_public_ip=not networking_stack.is_production,
            task_subnets=task_subnets,
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

        # ALB health check — ECS replaces tasks that fail this check
        self.service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200"
        )

        # Expose ALB for downstream stacks (observability alarms, incident response)
        self.alb = self.service.load_balancer
