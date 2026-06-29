import aws_cdk.assertions as assertions


def test_redriver_lambda_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "FunctionName": assertions.Match.string_like_regexp("dlq-redriver")
    })


def test_redriver_runtime_is_python312(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.12"
    })


def test_redriver_xray_tracing_active(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "TracingConfig": {"Mode": "Active"}
    })


def test_redriver_has_dlq_url_env_var(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {
            "Variables": assertions.Match.object_like({
                "DLQ_URL": assertions.Match.any_value()
            })
        }
    })


def test_three_eventbridge_rules_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.resource_count_is("AWS::Events::Rule", 3)


def test_ecs_stopped_rule_exists(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Events::Rule", {
        "Name": assertions.Match.string_like_regexp("ecs-task-stopped")
    })


def test_dlq_poll_schedule_is_5_min(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Events::Rule", {
        "ScheduleExpression": "rate(5 minutes)"
    })


def test_heartbeat_schedule_is_15_min(app_stacks):
    template = assertions.Template.from_stack(app_stacks["incident_response"])
    template.has_resource_properties("AWS::Events::Rule", {
        "ScheduleExpression": "rate(15 minutes)"
    })
