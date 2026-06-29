import os
import sys
import pytest
import aws_cdk as cdk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack
from stacks.streaming_stack import StreamingStack
from stacks.processing_stack import ProcessingStack
from stacks.compute_stack import ComputeStack
from stacks.observability_stack import ObservabilityStack
from stacks.incident_response_stack import IncidentResponseStack


@pytest.fixture(scope="session")
def app_stacks():
    # Skip Docker bundling during unit tests
    app = cdk.App(context={"aws:cdk:bundling-stacks": []})
    env = cdk.Environment(region="us-east-1", account="123456789012")

    app_name = "orders"
    stage = "test"
    component = "kinesis-archive"

    networking = NetworkingStack(app, "Networking", app_name=app_name, stage=stage, env=env)
    storage = StorageStack(app, "Storage", app_name=app_name, stage=stage, component=component, env=env)
    streaming = StreamingStack(app, "Streaming", app_name=app_name, stage=stage, storage_stack=storage, env=env)
    processing = ProcessingStack(app, "Processing", app_name=app_name, stage=stage, streaming_stack=streaming, storage_stack=storage, env=env)
    compute = ComputeStack(app, "Compute", app_name=app_name, stage=stage, networking_stack=networking, storage_stack=storage, streaming_stack=streaming, env=env)
    observability = ObservabilityStack(app, "Observability", app_name=app_name, stage=stage, processing_stack=processing, streaming_stack=streaming, storage_stack=storage, compute_stack=compute, env=env)
    incident_response = IncidentResponseStack(app, "IncidentResponse", app_name=app_name, stage=stage, processing_stack=processing, observability_stack=observability, compute_stack=compute, env=env)

    return {
        "networking": networking,
        "storage": storage,
        "streaming": streaming,
        "processing": processing,
        "compute": compute,
        "observability": observability,
        "incident_response": incident_response,
    }


@pytest.fixture(scope="session")
def prod_stacks():
    """Prod-stage fixture: enables private subnets, VPC endpoints, and isolated task placement."""
    app = cdk.App(context={"aws:cdk:bundling-stacks": []})
    env = cdk.Environment(region="us-east-1", account="123456789012")

    app_name = "orders"
    stage = "prod"
    component = "kinesis-archive"

    networking = NetworkingStack(app, "ProdNetworking", app_name=app_name, stage=stage, env=env)
    storage = StorageStack(app, "ProdStorage", app_name=app_name, stage=stage, component=component, env=env)
    streaming = StreamingStack(app, "ProdStreaming", app_name=app_name, stage=stage, storage_stack=storage, env=env)
    compute = ComputeStack(app, "ProdCompute", app_name=app_name, stage=stage, networking_stack=networking, storage_stack=storage, streaming_stack=streaming, env=env)

    return {
        "networking": networking,
        "storage": storage,
        "compute": compute,
    }
