import aws_cdk.assertions as assertions


def test_sns_topic_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.resource_count_is("AWS::SNS::Topic", 1)


def test_sns_topic_name(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.has_resource_properties("AWS::SNS::Topic", {
        "TopicName": "orders-test-alerts"
    })


def test_six_alarms_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.resource_count_is("AWS::CloudWatch::Alarm", 6)


def test_all_alarms_treat_missing_not_breaching(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    alarms = template.find_resources("AWS::CloudWatch::Alarm")
    for logical_id, resource in alarms.items():
        treat_missing = resource["Properties"].get("TreatMissingData")
        assert treat_missing == "notBreaching", (
            f"Alarm {logical_id} has TreatMissingData={treat_missing!r}, expected 'notBreaching'"
        )


def test_lambda_errors_alarm_threshold(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.has_resource_properties("AWS::CloudWatch::Alarm", {
        "AlarmName": assertions.Match.string_like_regexp("lambda-errors"),
        "Threshold": 1
    })


def test_dlq_depth_alarm_threshold(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.has_resource_properties("AWS::CloudWatch::Alarm", {
        "AlarmName": assertions.Match.string_like_regexp("dlq-depth"),
        "Threshold": 1
    })


def test_dashboard_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["observability"])
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)
