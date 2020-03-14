from aws_cdk import (
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    core
)

from aws_cdk.core import Tag

class AppInfraBaseStack(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(self, "stock-advisor-vpc",
            max_azs=3,
            cidr="192.168.0.0/16",
            subnet_configuration=[ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC,
                name="Public",
                cidr_mask=19
            )
            ]
        )

        Tag.add(self.vpc, "Name", "stock-advisor-vpc")
        Tag.add(self.vpc.public_subnets[0], "Name", "stock-advisor-subnet-1")
        Tag.add(self.vpc.public_subnets[1], "Name", "stock-advisor-subnet-2")
    
        repo_name = "stock-advisor-docker-repo"
        self.repository = ecr.Repository(self, repo_name, repository_name=repo_name)
        Tag.add(self.repository, "Name", repo_name)
        
        
        bucket = s3.Bucket(
            self, "stock-advisor-data"
        )

        '''
            Exports
        '''
        core.CfnOutput(self, "vpcid",
                       value=self.vpc.vpc_id)
        core.CfnOutput(self, "subnet1",
                       value=self.vpc.public_subnets[0].subnet_id)
        core.CfnOutput(self, "subnet2",
                       value=self.vpc.public_subnets[1].subnet_id)

        core.CfnOutput(
            self, "databucketname",
            description="Data bucket name",
            value=bucket.bucket_name,
        )

        core.CfnOutput(
            self, "dockerreponame",
            description="Docker Repository URI",
            value=self.repository.repository_uri,
        )


class AppInfraComputeStack(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, vpc: object, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.fargate_cluster = ecs.Cluster(
            self, 'stock-advisor-cluster',
            vpc = vpc
        )

        Tag.add(self.fargate_cluster, "Name", "stock-advisor-cluste")
    

        