"""Author: Mark Hanegraaff -- 2020
"""
from aws_cdk import (
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    core
)

from app_infra import util


class AppInfraComputeStack(core.Stack):
    """
        A CDK Stack representing the compute stack of the application
        
        See the project's readme.md for a complete description of the
        resources created here.
    """

    def __init__(self, scope: core.Construct, id: str, props: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        r_a_prefix = util.get_region_acct_prefix(kwargs['env'])
        APPLICATION_PREFIX = props['APPLICATION_PREFIX']

        repo_name = "%s-recommendation-service" % APPLICATION_PREFIX
        repo_description = "%s Recommendation Service" % APPLICATION_PREFIX
        self.repo_recommendation_service = ecr.Repository(self, repo_name, repository_name=repo_name, removal_policy=core.RemovalPolicy.DESTROY)
        util.tag_resource(self.repo_recommendation_service, repo_name, repo_description)

        policy_name = "policy-%s-ecs-task-execution" % APPLICATION_PREFIX
        docker_exec_policy = iam.ManagedPolicy(self, policy_name)
        docker_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "ec2:AttachNetworkInterface",
                "ec2:CreateNetworkInterface",
                "ec2:CreateNetworkInterfacePermission",
                "ec2:DeleteNetworkInterface",
                "ec2:DeleteNetworkInterfacePermission",
                "ec2:Describe*",
                "ec2:DetachNetworkInterface",
                "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
                "elasticloadbalancing:DeregisterTargets",
                "elasticloadbalancing:Describe*",
                "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
                "elasticloadbalancing:RegisterTargets",
                "route53:ChangeResourceRecordSets",
                "route53:CreateHealthCheck",
                "route53:DeleteHealthCheck",
                "route53:Get*",
                "route53:List*",
                "route53:UpdateHealthCheck",
                "servicediscovery:DeregisterInstance",
                "servicediscovery:Get*",
                "servicediscovery:List*",
                "servicediscovery:RegisterInstance",
                "servicediscovery:UpdateInstanceCustomHealthStatus"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["*"]
        ))
        docker_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "cloudwatch:DeleteAlarms",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:PutMetricAlarm"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:cloudwatch:%s:alarm:*" % r_a_prefix]
        ))
        docker_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "ec2:CreateTags"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:ec2:%s:network-interface/*" % r_a_prefix]
        ))
        docker_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "logs:CreateLogGroup",
                "logs:DescribeLogGroups",
                "logs:PutRetentionPolicy"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:logs:%s:log-group:/aws/ecs/*" % r_a_prefix]
        ))
        docker_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:logs:%s:log-group:/aws/ecs/*:log-stream:*" % r_a_prefix]
        ))
        
        exec_role_name = "role-%s-ecs-task-execution" % APPLICATION_PREFIX
        self.ecs_task_exec_role = iam.Role(
            self, exec_role_name, assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"), description="%s Execution role assumed by ECS" % APPLICATION_PREFIX, 
            managed_policies=[docker_exec_policy], 
            role_name=exec_role_name)
        
        self.recommendation_service_task = ecs.FargateTaskDefinition(
                self, "%s-recommendation-service-task" % APPLICATION_PREFIX, cpu=512, memory_limit_mib=1024, 
                execution_role=self.ecs_task_exec_role, family=None, task_role=props['ecs_task_role']
        )
        self.recommendation_service_task.add_container(
            "recommendation-service-container", 
            image=ecs.ContainerImage.from_ecr_repository(self.repo_recommendation_service, "latest"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=APPLICATION_PREFIX,
                log_group=logs.LogGroup(
                    self, "recommendation-service-loggroup",
                    log_group_name="sa/ecs/recommendation-service",
                    retention=logs.RetentionDays.ONE_MONTH,
                    removal_policy=core.RemovalPolicy.DESTROY
                )
            )
        )

        '''
            Outputs
        '''
        self.output_props = props.copy()
        self.output_props['repo_recommendation_service']= self.repo_recommendation_service
    
    @property
    def outputs(self):
        return self.output_props