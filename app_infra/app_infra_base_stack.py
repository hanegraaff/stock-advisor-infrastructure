"""Author: Mark Hanegraaff -- 2020
"""

from aws_cdk import (
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    core
)

from app_infra import util

class AppInfraBaseStack(core.Stack):
    """
        A CDK Stack representing the base resources for the application
        
        See the project's readme.md for a complete description of the
        resources created here.
    """
    
    def __init__(self, scope: core.Construct, id: str, props: dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        APPLICATION_PREFIX = props['APPLICATION_PREFIX']

        bucket_name = "%s-data-bucket" % APPLICATION_PREFIX
        bucket_description = "%s application data" % APPLICATION_PREFIX
        self.bucket = s3.Bucket(self, bucket_name)
        util.tag_resource(self.bucket, bucket_name, bucket_description)

        task_role_name = "role-%s-ecs-tasks" % APPLICATION_PREFIX
        self.ecs_task_role = iam.Role(
            self, task_role_name, assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"), description="AWS permissions shared by %s docker tasks" % APPLICATION_PREFIX, 
            role_name=task_role_name)

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

        cluster_name = "%s-docker-cluster" % APPLICATION_PREFIX
        cluster_description = "%s ECS cluster for all docker tasks" % APPLICATION_PREFIX
        self.fargate_cluster = ecs.Cluster(self, cluster_name, vpc = self.vpc
        )
        util.tag_resource(self.fargate_cluster, cluster_name, cluster_description)

        '''
            Exports
        '''
        core.CfnOutput(
            self, "databucketname", description="Data Bucket Name",
            value=self.bucket.bucket_name, export_name="%s-data-bucket-name" % APPLICATION_PREFIX
        )

        core.CfnOutput(self, "vpcid", description="VPC ID",
                       value=self.vpc.vpc_id, export_name="%s-vpcid" % APPLICATION_PREFIX)
        core.CfnOutput(self, "subnet1", description="Public Subnet 1",
                       value=self.vpc.public_subnets[0].subnet_id, export_name="%s-public-subnet-1" % APPLICATION_PREFIX)
        core.CfnOutput(self, "subnet2", description="Public Subnet 2",
                       value=self.vpc.public_subnets[1].subnet_id, export_name="%s-public-subnet-2" % APPLICATION_PREFIX)

        '''
            Outputs
        '''
        self.output_props = props.copy()
        self.output_props['ecs_task_role']= self.ecs_task_role

    @property
    def outputs(self):
        return self.output_props