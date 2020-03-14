import json
import pytest

from aws_cdk import core
from app_infra.app_infra_stack import AppInfraBaseStack


def get_template():
    app = core.App()
    AppInfraBaseStack(app, "app-infra-base")
    return json.dumps(app.synth().get_stack("app-infra-base").template)


def test_s3_created():
    assert("AWS::S3::Bucket" in get_template())


def test_s3_name():
    assert("databucketname" in get_template())