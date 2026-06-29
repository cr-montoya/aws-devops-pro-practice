import aws_cdk.assertions as assertions


def test_kinesis_stream_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["streaming"])
    template.resource_count_is("AWS::Kinesis::Stream", 1)


def test_stream_mode_on_demand(app_stacks):
    template = assertions.Template.from_stack(app_stacks["streaming"])
    template.has_resource_properties("AWS::Kinesis::Stream", {
        "StreamModeDetails": {"StreamMode": "ON_DEMAND"}
    })


def test_stream_encryption_enabled(app_stacks):
    template = assertions.Template.from_stack(app_stacks["streaming"])
    template.has_resource_properties("AWS::Kinesis::Stream", {
        "StreamEncryption": assertions.Match.object_like({
            "EncryptionType": assertions.Match.any_value()
        })
    })


def test_firehose_delivery_stream_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["streaming"])
    template.resource_count_is("AWS::KinesisFirehose::DeliveryStream", 1)


def test_firehose_s3_prefix(app_stacks):
    template = assertions.Template.from_stack(app_stacks["streaming"])
    template.has_resource_properties("AWS::KinesisFirehose::DeliveryStream", {
        "ExtendedS3DestinationConfiguration": assertions.Match.object_like({
            "Prefix": assertions.Match.string_like_regexp("raw/year=")
        })
    })
