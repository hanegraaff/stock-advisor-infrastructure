import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="app_infra",
    version="0.0.1",

    description="Infrastructure CDK template for Stock Advisor Application",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "app_infra"},
    packages=setuptools.find_packages(where="app_infra"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws_iam",
        "aws-cdk.aws_sns",
        "aws-cdk.aws_sns_subscriptions",
        "aws-cdk.aws-ec2",
        "aws-cdk.aws_s3",
        "aws-cdk.aws_ecs",
        "aws-cdk.aws_ecs_patterns",
        "aws-cdk.aws_ecr",
        "aws-cdk.aws_sns",
        "aws-cdk.aws_codebuild"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
