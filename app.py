#!/usr/bin/env python3

from aws_cdk import core

from app_infra.app_infra_stack import AppInfraBaseStack
from app_infra.app_infra_stack import AppInfraComputeStack


app = core.App()
base_stack = AppInfraBaseStack(app, "app-infra-base", env={'region': 'us-east-1'})
AppInfraComputeStack(app, "app-infra-compute", vpc=base_stack.vpc, env={'region': 'us-east-1'})

app.synth()
