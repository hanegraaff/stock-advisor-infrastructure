#!/usr/bin/env python3

from aws_cdk import core

from app_infra.app_infra_stack import AppInfraStack


app = core.App()
AppInfraStack(app, "app-infra", env={'region': 'us-west-2'})

app.synth()
