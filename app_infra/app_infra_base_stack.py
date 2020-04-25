"""Author: Mark Hanegraaff -- 2020
"""

from aws_cdk import (
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_sns as sns,
    core
)

from app_infra import util

class AppInfraBaseStack(core.Stack):
    """
        A CDK Stack representing the base resources for the application
        
        See the project's readme.md for a complete description of the
        resources created here.
    """
    
    def __init__(self, scope: core.Construct, id: str, props: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        APPLICATION_PREFIX = props['APPLICATION_PREFIX']

        '''
            S3 Data Bucket
        '''
        bucket_name = "%s-data-bucket" % APPLICATION_PREFIX
        bucket_description = "%s application data" % APPLICATION_PREFIX
        self.bucket = s3.Bucket(self, bucket_name, removal_policy=core.RemovalPolicy.DESTROY)
        
        util.tag_resource(self.bucket, bucket_name, bucket_description)

        '''
            SNS Topic used for application notifications and events
        '''
        sns_topic_name = "%s-app-notifications-topic" % APPLICATION_PREFIX
        self.notification_topic = sns.Topic(
            self, sns_topic_name, display_name=sns_topic_name, topic_name=sns_topic_name
        )

        util.tag_resource(self.notification_topic, sns_topic_name, "SNS Topic used for application notifications and events")



        '''
            IAM Role and Policy used to define permissions for ECS tasks
        '''
        policy_name = "policy-%s-ecs-tasks" % APPLICATION_PREFIX
        ecs_tasks_policy = iam.ManagedPolicy(self, policy_name)
        ecs_tasks_policy.add_statements(iam.PolicyStatement(actions=[
                "cloudformation:Describe*",
                "cloudformation:List*"
            ], conditions=None, effect=iam.Effect.ALLOW, resources=["*"]
        ))
        ecs_tasks_policy.add_statements(iam.PolicyStatement(actions=[
                "s3:*",
            ], conditions=None, effect=iam.Effect.ALLOW, resources=[self.bucket.bucket_arn+"/*"]
        )),
        ecs_tasks_policy.add_statements(iam.PolicyStatement(actions=[
                "sns:*",
            ], conditions=None, effect=iam.Effect.ALLOW, resources=[self.notification_topic.topic_arn]
        ))

        task_role_name = "role-%s-ecs-tasks" % APPLICATION_PREFIX
        self.ecs_task_role = iam.Role(
            self, task_role_name, assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"), description="AWS permissions shared by %s docker tasks" % APPLICATION_PREFIX, 
            role_name=task_role_name,
            managed_policies=[ecs_tasks_policy])

        util.tag_resource(self.ecs_task_role, task_role_name, "IAM Role and Policy used to define permissions for ECS tasks")

        '''
            VPC using by ECS Cluster
        '''

        self.vpc = ec2.Vpc(self, "%s-vpc" % APPLICATION_PREFIX,
            max_azs=3,
            cidr="192.168.0.0/17",
            subnet_configuration=[ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC,
                cidr_mask=20,
                name="public-subnet"
            )
            ]
        )

        util.tag_resource(self.vpc, "%s-vpc" % APPLICATION_PREFIX, "%s vpc for all container tasks" % APPLICATION_PREFIX)
        util.tag_resource(self.vpc.public_subnets[0], "%s-pub-subnet-1" % APPLICATION_PREFIX, "%s public subnet 1" % APPLICATION_PREFIX)
        util.tag_resource(self.vpc.public_subnets[1], "%s-pub-subnet-1" % APPLICATION_PREFIX, "%s public subnet 2" % APPLICATION_PREFIX)

        sg_name = "%s-sg" % APPLICATION_PREFIX
        sg_description = "%s security Group for ECS tasks" % APPLICATION_PREFIX
        self.sg = ec2.SecurityGroup(
            self, sg_name, vpc=self.vpc, allow_all_outbound=True, 
            description=sg_description, security_group_name=sg_name
        )
        util.tag_resource(self.sg, sg_name,sg_description)

        cluster_name = "%s-applicaton-cluster" % APPLICATION_PREFIX
        cluster_description = "%s ECS cluster for all applicaton tasks" % APPLICATION_PREFIX
        self.fargate_cluster = ecs.Cluster(self, cluster_name, vpc = self.vpc
        )
        
        util.tag_resource(self.fargate_cluster, cluster_name, cluster_description)

        '''
            Exports
        '''
        core.CfnOutput(
            self, "%s-databucketname"  % APPLICATION_PREFIX, description="Data Bucket Name",
            value=self.bucket.bucket_name, export_name=bucket_name + "-name"
        )

        core.CfnOutput(
            self, "%s-appnotificationstopic" % APPLICATION_PREFIX, description="%s SNS Topic for Application Notifications" % APPLICATION_PREFIX.upper(),
            value=self.notification_topic.topic_arn, export_name=sns_topic_name + "-name"
        )

        '''
            Outputs
        '''
        self.output_props = props.copy()
        self.output_props['vpc'] = self.vpc
        self.output_props['ecs_fargate_task_cluster'] = self.fargate_cluster
        self.output_props['ecs_task_role']= self.ecs_task_role

    @property
    def outputs(self):
        return self.output_props