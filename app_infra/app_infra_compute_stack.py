"""Author: Mark Hanegraaff -- 2020
"""
from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_applicationautoscaling as asg,
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

        self.output_props = props.copy()
        self.props = props

        r_a_prefix = util.get_region_acct_prefix(kwargs['env'])
        self.APPLICATION_PREFIX = self.props['APPLICATION_PREFIX']

        '''
            ECR Repo
        '''
        self.repo_recommendation_service = self.make_ecr_repo("recommendation-service", "Recommendation Service")
        self.rep_portfolio_manager = self.make_ecr_repo("portfolio-manager-service", "Portfolio Manager Service")

        '''
            IAM Role and Policy used by Fargate to execute task
        '''
        policy_name = "policy-%s-ecs-task-execution" % self.APPLICATION_PREFIX
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
        
        exec_role_name = "role-%s-ecs-task-execution" % self.APPLICATION_PREFIX
        self.ecs_task_exec_role = iam.Role(
            self, exec_role_name, assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"), description="%s Execution role assumed by ECS" % self.APPLICATION_PREFIX, 
            managed_policies=[docker_exec_policy], 
            role_name=exec_role_name
        )
        util.tag_resource(self.ecs_task_exec_role, exec_role_name, "IAM Role and Policy used by Fargate to execute task")


        '''
            Parameter Store variables:
            Intrinio API Key
            TDAMeritrade Client ID and Refresh Token
        '''
        intrinio_api_key_name = 'INTRINIO_API_KEY'
        self.intrinio_api_key_param = self.make_ssm_parameter(intrinio_api_key_name, 'put_api_key_here', 'API Key used to access Intrinio financial data')
        
        td_ameritrade_account_id_name = 'TDAMERITRADE_ACCOUNT_ID'
        self.tdameritrade_account_id = self.make_ssm_parameter(td_ameritrade_account_id_name, 'put_account_id_here', 'The TDAmeritrade Account ID')
        

        td_ameritrade_client_id_name = 'TDAMERITRADE_CLIENT_ID'
        self.tdameritrade_client_id = self.make_ssm_parameter(td_ameritrade_client_id_name, 'put_client_id_here', 'The Client Key used to authenticate the application')
        
        
        td_ameritrade_refresh_token_name = 'TDAMERITRADE_REFRESH_TOKEN'
        self.tdameritrade_refresh_token = self.make_ssm_parameter(td_ameritrade_refresh_token_name, 'put_refresh_token_here', 'OAuth refresh token used to generate temporary Access Keys')


        '''
            Fargate Tasks:
                1) Recommendation Service
                2) Portfolio Manager
        '''

        self.make_fargate_scheduled_task( 
            "recommendation-service", 
            "Recommendation service task definition",
            self.repo_recommendation_service,
            "/ecs/recommendation-service",
            ['-app_namespace', self.APPLICATION_PREFIX],
            {intrinio_api_key_name: ecs.Secret.from_ssm_parameter(self.intrinio_api_key_param)},
            "Recommendation service monthly scheduled task",
            "cron(0 10 ? * MON-FRI *)"
        )

        self.make_fargate_scheduled_task( 
            "portfolio-manager-service", 
            "Portfolio Manager service task definition",
            self.rep_portfolio_manager,
            "/ecs/portfolio-manager",
            ['-app_namespace', self.APPLICATION_PREFIX, "-portfolio_size", "3"],
            {
                intrinio_api_key_name: ecs.Secret.from_ssm_parameter(self.intrinio_api_key_param),
                td_ameritrade_account_id_name: ecs.Secret.from_ssm_parameter(self.tdameritrade_account_id),
                td_ameritrade_client_id_name: ecs.Secret.from_ssm_parameter(self.tdameritrade_client_id),
                td_ameritrade_refresh_token_name: ecs.Secret.from_ssm_parameter(self.tdameritrade_refresh_token)
            },
            "Portfolio Manager daily task",
            "cron(0 15 ? * MON-FRI *)"
        )


        '''
            Outputs
        '''
        self.output_props['repo_recommendation_service']= self.repo_recommendation_service
        self.output_props['repo_portfolio_manager'] = self.rep_portfolio_manager
    
    @property
    def outputs(self):
        return self.output_props

    def make_ssm_parameter(self, base_param_name : str, param_value : str, description : str):
        '''
            Creates and tags an SSM Parameter

            Parameters
            ----------
            base_param_name : str
                The base parameter name, wihtout the application namespace prefix
            param_value : str
                parameter value
            description : str
                parameter description 
        '''

        param = ssm.StringParameter(
            self, base_param_name, parameter_name="%s_%s" % (self.APPLICATION_PREFIX.upper(), base_param_name), string_value=param_value,
            description=description
            #,type=ssm.ParameterType.SECURE_STRING
        )
        util.tag_resource(param, base_param_name, description)

        return param


    def make_ecr_repo(self, repo_suffix : str, repo_description : str):
        '''
            Creates an ECR repo

            Parameters
            ----------
            repo_suffix : str
                The suffix of the repo. The full repo name is
                APPLICATION_PREFIX _ repo_suffix
        '''
        repo_name = "%s-%s" % (self.APPLICATION_PREFIX, repo_suffix)
        repo_description = "%s %s" % (self.APPLICATION_PREFIX, repo_description)
        ecr_repo = ecr.Repository(self, repo_name, repository_name=repo_name, removal_policy=core.RemovalPolicy.DESTROY)
        util.tag_resource(ecr_repo, repo_name, repo_description)

        return ecr_repo

        

    def make_fargate_scheduled_task(
            self, 
            scheduled_task_name : str,
            task_definition_description : str,
            task_ecr_repo : object,
            cloudwatch_loggroup_name : str,
            container_commands : list,
            container_secrets : dict,
            scheduled_task_description : str,
            scheduled_task_cron_expression : str
        ):

        '''
            Creates a Fargate Task definition, then scheduled task and associates it
            with the ECS cluster, applied tags, etc.

            Parameters
            ----------
            scheduled_task_name : str
                The name of the contsruct being created. Used to form the names
                of the various resources
            task_definition_description : str
                Description used for tags
            cloudwatch_loggroup_name : str
                Name of log group used by the container
            container_commands : str
                List of commands supplied to the container
            container_secrets : str
                Secrets supplied to the container
            scheduled_task_description : str
                Description used for tags
            scheduled_task_cron_expression : str
                Task schedule's chron expresion
        '''

        task_definition_name = "%s-%s-task-definition" % (self.APPLICATION_PREFIX, scheduled_task_name)
        fargate_task = ecs.FargateTaskDefinition(
            self, task_definition_name, cpu=512, memory_limit_mib=1024,
            execution_role=self.ecs_task_exec_role, family=None, task_role=self.props['ecs_task_role'],
        )

        fargate_task.add_container(
            "%s-%s-container" % (self.APPLICATION_PREFIX, scheduled_task_name), 
            image=ecs.ContainerImage.from_ecr_repository(task_ecr_repo, "latest"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=self.APPLICATION_PREFIX,
                log_group=logs.LogGroup(
                    self, "%s-%s-cloudwatch-loggroup" % (self.APPLICATION_PREFIX, scheduled_task_name),
                    log_group_name="%s%s" % (self.APPLICATION_PREFIX, cloudwatch_loggroup_name),
                    retention=logs.RetentionDays.ONE_MONTH,
                    removal_policy=core.RemovalPolicy.DESTROY
                )
            ),
            command=container_commands,
            secrets=container_secrets
        )
        util.tag_resource(fargate_task, task_definition_name, task_definition_description)

        scheduled_task_name = "%s-%s-scheduled-task" % (self.APPLICATION_PREFIX, scheduled_task_name)
        ecs_sched_task = ecs_patterns.ScheduledFargateTask(
            self, scheduled_task_name,
            scheduled_fargate_task_definition_options=ecs_patterns.ScheduledFargateTaskDefinitionOptions(
                task_definition=fargate_task
            ),
            schedule=asg.Schedule.expression(scheduled_task_cron_expression),
            cluster=self.props['ecs_fargate_task_cluster'],
            vpc=self.props['ecs_fargate_task_cluster'],
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType(ec2.SubnetType.PUBLIC))
        )

        util.tag_resource(ecs_sched_task, scheduled_task_name, scheduled_task_description)
