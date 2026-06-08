import aws_cdk as cdk
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from aws_cdk import aws_logs as logs
from constructs import Construct


class ObservabilityStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        stage: str,
        processing_stack: "ProcessingStack",
        streaming_stack: "StreamingStack",
        storage_stack: "StorageStack",
        compute_stack: "ComputeStack",
        alert_emails: list = [],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SNS topic — single sink for all alarms and EventBridge rules.
        # Reused by IncidentResponseStack so all notifications go through one channel.
        self.alerts_topic = sns.Topic(self, "AlertsTopic",
            topic_name=f"{app_name}-{stage}-alerts",
            display_name=f"{app_name}-{stage} Alerts"
        )
        # Email subscriptions require manual confirmation after deploy — check inbox for AWS SNS confirmation link
        for email in alert_emails:
            self.alerts_topic.add_subscription(subscriptions.EmailSubscription(email))

        sns_action = cw_actions.SnsAction(self.alerts_topic)

        # --- Alarms ---
        # TreatMissingData.NOT_BREACHING: no traffic = no data = no alarm.
        # Prevents false positives in dev when the pipeline is idle (nights/weekends).

        # Any Lambda error fires immediately — stream processing errors are not expected
        lambda_errors = cloudwatch.Alarm(self, "LambdaErrors",
            alarm_name=f"{app_name}-{stage}-lambda-errors",
            metric=processing_stack.processor.metric_errors(
                period=cdk.Duration.minutes(1),
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Lambda processor error count >= 1"
        )
        lambda_errors.add_alarm_action(sns_action)

        # p95 at 45s warns before hard timeout at 60s — gives time to investigate before Lambda starts killing executions
        lambda_duration = cloudwatch.Alarm(self, "LambdaDuration",
            alarm_name=f"{app_name}-{stage}-lambda-duration-p95",
            metric=processing_stack.processor.metric_duration(
                period=cdk.Duration.minutes(5),
                statistic="p95"
            ),
            threshold=45000,
            evaluation_periods=3,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Lambda p95 duration >= 45s (75% of 60s timeout)"
        )
        lambda_duration.add_alarm_action(sns_action)

        # Throttles mean Lambda hit concurrency limits — scale up reserved concurrency or reduce batch size
        lambda_throttles = cloudwatch.Alarm(self, "LambdaThrottles",
            alarm_name=f"{app_name}-{stage}-lambda-throttles",
            metric=processing_stack.processor.metric_throttles(
                period=cdk.Duration.minutes(1),
                statistic="Sum"
            ),
            threshold=1,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Lambda throttles detected"
        )
        lambda_throttles.add_alarm_action(sns_action)

        # IteratorAge measures how far behind the consumer is from the tip of the stream.
        # >= 60s over 3 evaluation periods (15 min total) means Lambda is not keeping up with producers.
        kds_iterator_age = cloudwatch.Alarm(self, "KdsIteratorAge",
            alarm_name=f"{app_name}-{stage}-kds-iterator-age",
            metric=cloudwatch.Metric(
                namespace="AWS/Kinesis",
                metric_name="GetRecords.IteratorAgeMilliseconds",
                dimensions_map={"StreamName": streaming_stack.stream.stream_name},
                period=cdk.Duration.minutes(5),
                statistic="Maximum"
            ),
            threshold=60000,
            evaluation_periods=3,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="KDS consumer falling behind >= 60s"
        )
        kds_iterator_age.add_alarm_action(sns_action)

        # Any message in the DLQ means Lambda exhausted all retries on a record.
        # This fires immediately (threshold=1) — DLQ depth should always be 0.
        dlq_depth = cloudwatch.Alarm(self, "DlqDepth",
            alarm_name=f"{app_name}-{stage}-dlq-depth",
            metric=cloudwatch.Metric(
                namespace="AWS/SQS",
                metric_name="ApproximateNumberOfMessagesVisible",
                dimensions_map={"QueueName": processing_stack.dlq.queue_name},
                period=cdk.Duration.minutes(1),
                statistic="Maximum"
            ),
            threshold=1,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="Messages in DLQ - Lambda is failing permanently"
        )
        dlq_depth.add_alarm_action(sns_action)

        # 5xx from target means the FastAPI container is returning errors (not ALB itself).
        # Threshold of 5 avoids alerting on transient single errors.
        alb_5xx = cloudwatch.Alarm(self, "Alb5xx",
            alarm_name=f"{app_name}-{stage}-alb-5xx",
            metric=cloudwatch.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="HTTPCode_Target_5XX_Count",
                dimensions_map={
                    "LoadBalancer": compute_stack.alb.load_balancer_full_name
                },
                period=cdk.Duration.minutes(1),
                statistic="Sum"
            ),
            threshold=5,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description="ALB target 5xx errors >= 5 in 1 minute"
        )
        alb_5xx.add_alarm_action(sns_action)

        # --- Log retention ---
        # CDK does not set retention on log groups by default (they stay forever).
        # LogRetention uses a custom resource (Lambda-backed) to call PutRetentionPolicy
        # on existing log groups without recreating them.
        logs.LogRetention(self, "LambdaLogRetention",
            log_group_name=f"/aws/lambda/{processing_stack.processor.function_name}",
            retention=logs.RetentionDays.ONE_MONTH
        )
        logs.LogRetention(self, "EcsLogRetention",
            log_group_name=f"/ecs/{app_name}-{stage}-web-service",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # --- Dashboard ---
        # 24-column grid: width=8 fits 3 widgets per row, width=12 fits 2 per row

        dashboard = cloudwatch.Dashboard(self, "Dashboard",
            dashboard_name=f"{app_name}-{stage}-dashboard"
        )

        # Row 1: Lambda health
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[processing_stack.processor.metric_invocations(
                    period=cdk.Duration.minutes(1), statistic="Sum"
                )],
                width=8
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[processing_stack.processor.metric_errors(
                    period=cdk.Duration.minutes(1), statistic="Sum"
                )],
                width=8
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration (p50 / p95)",
                left=[
                    processing_stack.processor.metric_duration(
                        period=cdk.Duration.minutes(1), statistic="p50", label="p50"
                    ),
                    processing_stack.processor.metric_duration(
                        period=cdk.Duration.minutes(1), statistic="p95", label="p95"
                    ),
                ],
                width=8
            ),
        )

        # Row 2: Stream health
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="KDS Iterator Age (ms)",
                left=[cloudwatch.Metric(
                    namespace="AWS/Kinesis",
                    metric_name="GetRecords.IteratorAgeMilliseconds",
                    dimensions_map={"StreamName": streaming_stack.stream.stream_name},
                    period=cdk.Duration.minutes(5),
                    statistic="Maximum"
                )],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="KDS Incoming Records",
                left=[cloudwatch.Metric(
                    namespace="AWS/Kinesis",
                    metric_name="IncomingRecords",
                    dimensions_map={"StreamName": streaming_stack.stream.stream_name},
                    period=cdk.Duration.minutes(1),
                    statistic="Sum"
                )],
                width=12
            ),
        )

        # Row 3: Infrastructure
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="DLQ Depth",
                left=[cloudwatch.Metric(
                    namespace="AWS/SQS",
                    metric_name="ApproximateNumberOfMessagesVisible",
                    dimensions_map={"QueueName": processing_stack.dlq.queue_name},
                    period=cdk.Duration.minutes(1),
                    statistic="Maximum"
                )],
                width=8
            ),
            cloudwatch.GraphWidget(
                title="ALB Request Count",
                left=[cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="RequestCount",
                    dimensions_map={
                        "LoadBalancer": compute_stack.alb.load_balancer_full_name
                    },
                    period=cdk.Duration.minutes(1),
                    statistic="Sum"
                )],
                width=8
            ),
            cloudwatch.GraphWidget(
                title="ALB 5xx Errors",
                left=[cloudwatch.Metric(
                    namespace="AWS/ApplicationELB",
                    metric_name="HTTPCode_Target_5XX_Count",
                    dimensions_map={
                        "LoadBalancer": compute_stack.alb.load_balancer_full_name
                    },
                    period=cdk.Duration.minutes(1),
                    statistic="Sum"
                )],
                width=8
            ),
        )
