import json
import pytest

from aws_cdk import core
from app_infra.app_infra_stack import AppInfraStack


def get_template():
    app = core.App()
    AppInfraStack(app, "app-infra")
    return json.dumps(app.synth().get_stack("app-infra").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())


def test_sns_topic_created():
    assert("AWS::SNS::Topic" in get_template())
