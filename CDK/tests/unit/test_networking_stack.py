import pytest
import aws_cdk.assertions as assertions


def test_vpc_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_public_subnets_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    resources = template.find_resources("AWS::EC2::Subnet", {
        "Properties": {"MapPublicIpOnLaunch": True}
    })
    assert len(resources) >= 2


def test_internet_gateway_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    template.resource_count_is("AWS::EC2::InternetGateway", 1)


@pytest.mark.skip(reason="pending VPC endpoints refactor — only created in prod stage")
def test_private_subnets_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    resources = template.find_resources("AWS::EC2::Subnet", {
        "Properties": {"MapPublicIpOnLaunch": False}
    })
    assert len(resources) >= 2


@pytest.mark.skip(reason="pending VPC endpoints refactor")
def test_s3_gateway_endpoint_exists(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "VpcEndpointType": "Gateway",
        "ServiceName": assertions.Match.string_like_regexp("s3")
    })


@pytest.mark.skip(reason="pending VPC endpoints refactor")
def test_interface_endpoints_count(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    resources = template.find_resources("AWS::EC2::VPCEndpoint", {
        "Properties": {"VpcEndpointType": "Interface"}
    })
    assert len(resources) >= 5


@pytest.mark.skip(reason="pending VPC endpoints refactor")
def test_endpoints_sg_allows_443(app_stacks):
    template = assertions.Template.from_stack(app_stacks["networking"])
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "SecurityGroupIngress": assertions.Match.array_with([
            assertions.Match.object_like({"FromPort": 443, "ToPort": 443})
        ])
    })
