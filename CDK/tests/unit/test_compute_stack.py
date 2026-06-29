import pytest
import aws_cdk.assertions as assertions


def test_ecs_cluster_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_fargate_service_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.resource_count_is("AWS::ECS::Service", 1)


def test_alb_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)


def test_alb_is_internet_facing(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.has_resource_properties("AWS::ElasticLoadBalancingV2::LoadBalancer", {
        "Scheme": "internet-facing"
    })


def test_container_port_is_8080(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": assertions.Match.array_with([
            assertions.Match.object_like({
                "PortMappings": assertions.Match.array_with([
                    assertions.Match.object_like({"ContainerPort": 8080})
                ])
            })
        ])
    })


def test_secret_created(app_stacks):
    template = assertions.Template.from_stack(app_stacks["compute"])
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_tasks_not_assigned_public_ip(prod_stacks):
    template = assertions.Template.from_stack(prod_stacks["compute"])
    resources = template.find_resources("AWS::ECS::Service", {
        "Properties": {
            "NetworkConfiguration": {
                "AwsvpcConfiguration": {"AssignPublicIp": "ENABLED"}
            }
        }
    })
    assert len(resources) == 0


def test_endpoint_sg_has_task_sg_ingress(prod_stacks):
    # CfnSecurityGroupIngress lives in the compute stack (not networking) to avoid
    # a circular cross-stack dependency. It targets endpoints_sg.group_id via import.
    template = assertions.Template.from_stack(prod_stacks["compute"])
    template.has_resource_properties("AWS::EC2::SecurityGroupIngress", {
        "FromPort": 443,
        "ToPort": 443,
        "IpProtocol": "tcp",
    })
