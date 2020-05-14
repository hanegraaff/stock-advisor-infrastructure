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
        self.APPLICATION_PREFIX = props['APPLICATION_PREFIX']
        self.GITHUB_REPO_OWNER = props['GITHUB_REPO_OWNER']
        self.GITHUB_REPO_NAME = props['GITHUB_REPO_NAME']

        '''
            IAM Role and Policy used by CodeBuild to execute build jobs
        '''
        policy_name = "policy-%s-codebuild-execution" % self.APPLICATION_PREFIX
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

        exec_role_name = "role-%s-codebuild-execution" % self.APPLICATION_PREFIX
        self.codebuild_role_name = iam.Role(
            self, exec_role_name, assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"), description="%s Execution role assumed by ECS" % self.APPLICATION_PREFIX, 
            managed_policies=[codebuild_exec_policy], 
            role_name=exec_role_name)

        '''
            CodeBuild build project
        '''
        self.make_codebuild_project(
            "recommendation-service-project", 
            "Project used to build the Recommendation Service",
            "config/buildspec-recommendation-svc.yml",
            {
                'RECOMMENDATION_SERVICE_REPO_URI': codebuild.BuildEnvironmentVariable(
                    value=props['repo_recommendation_service'].repository_uri)
            }
        )

        self.make_codebuild_project(
            "portfolio-manager-project", 
            "Project used to build the Portfolio Manager",
            "config/buildspec-portfolio-manager.yml",
            {
                'PORTFOLIOMGR_SERVICE_REPO_URI': codebuild.BuildEnvironmentVariable(
                    value=props['repo_portfolio_manager'].repository_uri)
            }
        )

    @property
    def outputs(self):
        return self.output_props

    def make_codebuild_project(
            self, project_suffix : str, 
            description : str,
            buildspec_path : str,
            env_variables : dict):
        '''
            Creates a codebuild project

            Parameters
            ----------
            project_suffix : str
                The suffix of the project. The full project name is
                APPLICATION_PREFIX _ project_suffix
            description : str
                Description used by tags
            buildspec_path : str
                the path the buildspec used to build this project
            env_variables : str
                The environment variables supplued to the project, e.g. the ECR epo URI
        '''

        project_name = "%s-%s" % (self.APPLICATION_PREFIX, project_suffix)
        build_project = codebuild.Project(
            self, project_name, 
            source=codebuild.Source.git_hub(owner=self.GITHUB_REPO_OWNER, repo=self.GITHUB_REPO_NAME),
            build_spec=codebuild.BuildSpec.from_source_filename(buildspec_path),
            description=description,
            environment_variables=env_variables,
            environment=codebuild.BuildEnvironment(
                privileged=True,
            ),
            project_name=project_name, role=self.codebuild_role_name,
            timeout=core.Duration.hours(1))

        util.tag_resource(build_project, project_name, description)

        