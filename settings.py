# Override any keys below by putting them in a local_settings.py. Some
# overrides are required, signaled by a #* on the same line.

import os

### Get these from: http://aws-portal.amazon.com/gp/aws/developer/account/index.html?action=access-key
aws_access_key = None #*
aws_secret_key = None #*

### aws security config
security_groups = None #*

### key pair name
key_pair_name = None #*

### path to ssh private key
### Will resolve ~
ec2_ssh_key = None #*
ec2_ssh_username = 'ubuntu' # ami specific
ec2_ssh_key_password = None # only required if your ssh key is encrypted

### five cannons is a healthy blast
num_cannons = 5

### Availbility zones: http://alestic.com/2009/07/ec2-availability-zones
placement = 'us-east-1a'

### ami key from: http://uec-images.ubuntu.com/releases/11.10/release/
ami_key = 'ami-a7f539ce'
instance_type = 't1.micro'

### enable cloud init, so that a second deploy step is not required
enable_cloud_init = True

### scripts for building environments
env_scripts_dir = os.path.abspath(os.path.dirname('./env_scripts/'))

### Siege config settings
siege_config = {
    'connection': 'close',
    'concurrency': 200,
    'internet': 'true',
    'time': '5M'
}

### Siege urls
# siege_urls = [
#     'http://localhost',
#     'http://localhost/test'
# ]

try:
    from local_settings import *
except:
    pass
