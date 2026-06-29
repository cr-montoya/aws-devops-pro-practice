import aws_cdk.assertions as assertions


def test_lambda_function_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_lambda_runtime_is_python312(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.12"
    })


def test_lambda_timeout_is_60s(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "Timeout": 60
    })


def test_lambda_memory_is_256mb(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "MemorySize": 256
    })


def test_lambda_xray_tracing_active(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "TracingConfig": {"Mode": "Active"}
    })


def test_lambda_has_table_name_env_var(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {
            "Variables": assertions.Match.object_like({
                "TABLE_NAME": assertions.Match.any_value()
            })
        }
    })


def test_kinesis_event_source_has_on_failure_dlq(app_stacks):
    # on_failure on the event source mapping is correct for stream-based sources (KDS).
    # dead_letter_queue on the function only applies to async invocations (SNS, S3, EventBridge).
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::Lambda::EventSourceMapping", {
        "DestinationConfig": assertions.Match.object_like({
            "OnFailure": assertions.Match.object_like({
                "Destination": assertions.Match.any_value()
            })
        })
    })


def test_dlq_retention_is_14_days(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::SQS::Queue", {
        "MessageRetentionPeriod": 1209600
    })


def test_lambda_role_has_basic_execution_policy(app_stacks):
    template = assertions.Template.from_stack(app_stacks["processing"])
    template.has_resource_properties("AWS::IAM::Role", {
        "ManagedPolicyArns": assertions.Match.array_with([
            assertions.Match.object_like({
                "Fn::Join": ["", assertions.Match.array_with([
                    assertions.Match.string_like_regexp("AWSLambdaBasicExecutionRole")
                ])]
            })
        ])
    })
