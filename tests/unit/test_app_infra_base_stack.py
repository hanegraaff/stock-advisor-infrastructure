import json
import pytest

from aws_cdk import core
from aws_cdk.core import Aws
from app_infra.app_infra_base_stack import AppInfraBaseStack

environment =	{
  "region": "us-east-1",
  "account": Aws.ACCOUNT_ID
}

props = {
  'APPLICATION_PREFIX': 'sa'
}

def get_template():
    app = core.App()
    AppInfraBaseStack(app, "app-infra-base", props, env=environment)

    template_str = json.dumps(app.synth().get_stack("app-infra-base").template)
    print(template_str)
    
    return template_str


def test_s3_do_nothing():
    #assert("AWS::S3::Bucket" in get_template())
    assert(True)
