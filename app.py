#!/usr/bin/env python3

from aws_cdk import core
from aws_cdk.core import Aws

from app_infra.app_infra_base_stack import AppInfraBaseStack
from app_infra.app_infra_compute_stack import AppInfraComputeStack
from app_infra.app_infra_develop_stack import AppInfraDevelopmentStack

environment =	{
  "region": "us-east-1",
  "account": Aws.ACCOUNT_ID
}

props = {
  'APPLICATION_PREFIX': 'sa'
}


app = core.App()
base    = AppInfraBaseStack(app, "app-infra-base", props=props, env=environment)
compute = AppInfraComputeStack(app, "app-infra-compute", props=base.outputs, env=environment)
develop = AppInfraDevelopmentStack(app, "app-infra-develop", props=compute.outputs, env=environment)

app.synth()
