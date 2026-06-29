import aws_cdk.assertions as assertions


def test_dynamodb_table_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["storage"])
    template.resource_count_is("AWS::DynamoDB::Table", 1)


def test_dynamodb_partition_key_is_id(app_stacks):
    template = assertions.Template.from_stack(app_stacks["storage"])
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "KeySchema": assertions.Match.array_with([
            {"AttributeName": "id", "KeyType": "HASH"}
        ])
    })


def test_dynamodb_billing_mode(app_stacks):
    template = assertions.Template.from_stack(app_stacks["storage"])
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST"
    })


def test_dynamodb_pitr_disabled_outside_prod(app_stacks):
    template = assertions.Template.from_stack(app_stacks["storage"])
    resources = template.find_resources("AWS::DynamoDB::Table", {
        "Properties": {
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": True
            }
        }
    })
    assert len(resources) == 0


def test_dynamodb_pitr_enabled_in_prod(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["storage"])
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "PointInTimeRecoverySpecification": {
            "PointInTimeRecoveryEnabled": True
        }
    })


def test_s3_bucket_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["storage"])
    template.resource_count_is("AWS::S3::Bucket", 1)
