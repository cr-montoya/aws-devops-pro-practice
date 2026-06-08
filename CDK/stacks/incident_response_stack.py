import aws_cdk as cdk
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from constructs import Construct


class IncidentResponseStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        processing_stack: "ProcessingStack",
        observability_stack: "ObservabilityStack",
        compute_stack: "ComputeStack",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- DLQ Re-driver Lambda ---
        # Reads up to 10 messages from the DLQ and re-invokes the processor directly.
        # Runs on a schedule (every 5 min) so failed records are retried without manual intervention.
        # Uses AWSLambdaBasicExecutionRole so it can write its own execution logs to CloudWatch.

        redriver_role = iam.Role(self, "RedriverRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        # grant_consume_messages grants ReceiveMessage + DeleteMessage + GetQueueAttributes
        processing_stack.dlq.grant_consume_messages(redriver_role)
        processing_stack.processor.grant_invoke(redriver_role)

        redriver = lambda_.Function(self, "DlqRedriver",
            function_name=f"{app_name}-{stage}-dlq-redriver",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda", bundling=cdk.BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                command=[
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output && cp -r . /asset-output"
                ],
            )),
            handler="dlq_redriver.handler",
            role=redriver_role,
            timeout=cdk.Duration.seconds(60),
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "DLQ_URL": processing_stack.dlq.queue_url,
                "PROCESSOR_FUNCTION_NAME": processing_stack.processor.function_name,
            }
        )

        # --- ECS Task Stopped Rule ---
        # Matches any task that stopped with an explicit stoppedReason (crashes, OOM, health check failures).
        # `exists: True` on stoppedReason excludes graceful replacements during rolling deployments
        # where the reason field may be absent.
        ecs_task_stopped_rule = events.Rule(self, "EcsTaskStoppedRule",
            rule_name=f"{app_name}-{stage}-ecs-task-stopped",
            description="Fires when an ECS task stops unexpectedly",
            event_pattern=events.EventPattern(
                source=["aws.ecs"],
                detail_type=["ECS Task State Change"],
                detail={
                    "clusterArn": [compute_stack.cluster.cluster_arn],
                    "lastStatus": ["STOPPED"],
                    "stoppedReason": [{"exists": True}]
                }
            )
        )
        ecs_task_stopped_rule.add_target(
            targets.SnsTopic(
                observability_stack.alerts_topic,
                message=events.RuleTargetInput.from_text(
                    f"[{app_name}-{stage}] ECS task stopped. "
                    "Reason: <detail.stoppedReason>. Task: <detail.taskArn>"
                )
            )
        )

        # --- DLQ Poll Schedule ---
        # Triggers the re-driver every 5 minutes. If the DLQ is empty, the re-driver
        # returns immediately with no side effects. No need to check depth before triggering.
        dlq_poll_rule = events.Rule(self, "DlqPollRule",
            rule_name=f"{app_name}-{stage}-dlq-poll",
            description="Triggers DLQ re-driver every 5 minutes",
            schedule=events.Schedule.rate(cdk.Duration.minutes(5))
        )
        dlq_poll_rule.add_target(targets.LambdaFunction(redriver))

        # --- Heartbeat Schedule ---
        # Publishes a message to SNS every 15 minutes to confirm the EventBridge bus is alive.
        # If the heartbeat stops arriving, it means EventBridge or SNS itself has a problem.
        heartbeat_rule = events.Rule(self, "HeartbeatRule",
            rule_name=f"{app_name}-{stage}-heartbeat",
            description="Publishes heartbeat to SNS every 15 minutes",
            schedule=events.Schedule.rate(cdk.Duration.minutes(15))
        )
        heartbeat_rule.add_target(
            targets.SnsTopic(
                observability_stack.alerts_topic,
                message=events.RuleTargetInput.from_text(
                    f"[{app_name}-{stage}] Scheduled health check - pipeline is running"
                )
            )
        )
