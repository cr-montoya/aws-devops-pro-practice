#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.networking_stack import NetworkingStack
from stacks.storage_stack import StorageStack

app = cdk.App()
env = cdk.Environment(region="us-east-2")

# Configuration
app_name = "orders"
stage = "dev"
component = "kinesis-archive"

# Stacks
NetworkingStack(app, "Networking", app_name=app_name, stage=stage, env=env)
StorageStack(app, "Storage", app_name=app_name, stage=stage, component=component, env=env)

app.synth()
