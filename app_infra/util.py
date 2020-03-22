"""Author: Mark Hanegraaff -- 2020

This module contains shared utilities used by the various stack classes
"""

from aws_cdk.core import Tag

def get_region_acct_prefix(env):
    """
        Returns a formatted region and account used to construct ARNs

        Parmeters
        ---------
        env : dict
            Environment dictionary defined in app.py

        Returns
        ---------
        A String containing the region and account. The region
        is currently defined as "*".
        e.g. ":1234567890"
        
    """
    return "*:%s" % (env['account'])

def tag_resource(resource: object, name: str, description: str):
    """
        Applied a consistent set of tags to a CDK resoource

        Parmeters
        ---------
        resource : object
            The CDK resource to be tagged

        name : str
            Value of the "name" tag
        
        description : str
            Value of the "description" tag

        Returns
        ---------
        None
        
    """
    Tag.add(resource, "name", name)
    Tag.add(resource, "description", description)