"""Author: Mark Hanegraaff -- 2020
"""
from aws_cdk import (
    aws_iam as iam,
    aws_codebuild as codebuild,
    core
)

from app_infra import util
      
class AppInfraDevelopmentStack(core.Stack):
    """
        A CDK Stack representing the development stack of the application.
        Note that this stack only contains the CICD automation constructs.
        
        See the project's readme.md for a complete description of the
        resources created here.
    """

    def __init__(self, scope: core.Construct, id: str, props: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        r_a_prefix = util.get_region_acct_prefix(kwargs['env'])
        APPLICATION_PREFIX = props['APPLICATION_PREFIX']

        '''
            IAM Role and Policy used by CodeBuild to execute build jobs
        '''
        policy_name = "policy-%s-codebuild-execution" % APPLICATION_PREFIX
        codebuild_exec_policy = iam.ManagedPolicy(self, policy_name)
        codebuild_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:logs:%s:log-group:/aws/codebuild/*" % r_a_prefix]
        ))
        codebuild_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:s3:::codepipeline*"]
        ))
        codebuild_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "codebuild:CreateReportGroup",
                "codebuild:CreateReport",
                "codebuild:UpdateReport",
                "codebuild:BatchPutTestCases"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:codebuild:%s:report-group/*" % r_a_prefix]
        ))
        codebuild_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "ecr:GetAuthorizationToken"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["*"]
        ))
        codebuild_exec_policy.add_statements(iam.PolicyStatement(actions=[
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:BatchCheckLayerAvailability",
                "ecr:PutImage"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["arn:aws:ecr:%s:repository/*" % r_a_prefix]
        ))

        exec_role_name = "role-%s-codebuild-execution" % APPLICATION_PREFIX
        self.codebuild_role_name = iam.Role(
            self, exec_role_name, assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"), description="%s Execution role assumed by ECS" % APPLICATION_PREFIX, 
            managed_policies=[codebuild_exec_policy], 
            role_name=exec_role_name)

        '''
            Recommendation Service CodeBuild project
        '''
        pfolio_sel_project_name = "%s-recommendation-service-project" % APPLICATION_PREFIX
        self.build_project = codebuild.Project(
            self, pfolio_sel_project_name, 
            source=codebuild.Source.git_hub(owner='hanegraaff', repo='stock-advisor'), 
            description="Recommendation Service Build Project",
            environment_variables={
                'RECOMMENDATION_SERVICE_REPO_URI': codebuild.BuildEnvironmentVariable(
                    value=props['repo_recommendation_service'].repository_uri)
            },
            environment=codebuild.BuildEnvironment(
                privileged=True,
            ),
            project_name=pfolio_sel_project_name, role=self.codebuild_role_name, 
            timeout=core.Duration.hours(1))

    @property
    def outputs(self):
        return self.output_props

        