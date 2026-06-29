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


def test_private_subnets_created(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["networking"])
    resources = template.find_resources("AWS::EC2::Subnet", {
        "Properties": {"MapPublicIpOnLaunch": False}
    })
    assert len(resources) >= 2


def test_s3_gateway_endpoint_exists(prod_stacks):
    # Gateway endpoints (S3, DynamoDB) use Fn::Join for the service name so
    # string_like_regexp cannot match them. Verify by VpcEndpointType instead.
    template = assertions.Template.from_stack(prod_stacks["networking"])
    resources = template.find_resources("AWS::EC2::VPCEndpoint", {
        "Properties": {"VpcEndpointType": "Gateway"}
    })
    assert len(resources) == 2  # S3 and DynamoDB


def test_interface_endpoints_count(prod_stacks):
    # ECR, ECR Docker, ECS, ECS Agent, ECS Telemetry, STS,
    # Secrets Manager, CloudWatch Logs, Kinesis = 9 interface endpoints
    template = assertions.Template.from_stack(prod_stacks["networking"])
    resources = template.find_resources("AWS::EC2::VPCEndpoint", {
        "Properties": {"VpcEndpointType": "Interface"}
    })
    assert len(resources) == 9


def test_endpoints_sg_allows_443(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["networking"])
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "SecurityGroupIngress": assertions.Match.array_with([
            assertions.Match.object_like({"FromPort": 443, "ToPort": 443})
        ])
    })


def test_public_nacl_allows_alb_to_private_tasks(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["networking"])
    template.has_resource_properties("AWS::EC2::NetworkAclEntry", {
        "CidrBlock": assertions.Match.any_value(),
        "Egress": True,
        "PortRange": {"From": 8080, "To": 8080},
        "Protocol": 6,
        "RuleAction": "allow",
    })


def test_private_nacl_allows_gateway_endpoint_https(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["networking"])
    template.has_resource_properties("AWS::EC2::NetworkAclEntry", {
        "CidrBlock": "0.0.0.0/0",
        "Egress": True,
        "PortRange": {"From": 443, "To": 443},
        "Protocol": 6,
        "RuleAction": "allow",
    })


def test_private_nacl_allows_gateway_endpoint_return_traffic(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["networking"])
    template.has_resource_properties("AWS::EC2::NetworkAclEntry", {
        "CidrBlock": "0.0.0.0/0",
        "Egress": False,
        "PortRange": {"From": 1024, "To": 65535},
        "Protocol": 6,
        "RuleAction": "allow",
    })
