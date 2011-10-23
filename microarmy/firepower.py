import eventlet
import boto
import time
import os
import yaml

from microarmy.communications import (
    ssh_connect,
    exec_command,
    put_file,
)

### Override any defaults in config.py with a local_config.py
from settings import (
    aws_access_key,
    aws_secret_key,
    security_groups,
    key_pair_name,
    num_cannons,
    placement,
    ami_key,
    instance_type,
    enable_cloud_init,
    env_scripts_dir,
)

pool = eventlet.GreenPool()


class UnparsableData(Exception):

    def __init__(self, value):
        self.data = value
    def __str__(self):
        return repr(self.data)

###
### Cannon functions
###

CANNON_INIT_SCRIPT = 'build_cannon.sh'
SIEGE_CONFIG = 'siegerc'
URLS = 'urls.txt'
CLOUD_INIT_DATA ={
    'apt_update': True,
    'packages':['siege'],
        #'python-dev', 'build-essential', 'autoconf', 'automake', 'libtool',
        #'uuid-dev', 'git-core', 'mercurial', 'python-pip'],
    'runcmd': [
        ['bash', '-c', "echo fs.file-max = 1000000 | tee -a /etc/sysctl.conf"],
        ['bash', '-c', "echo ubuntu  soft  nofile  1000000 | tee -a /etc/security/limits.conf"],
        ['bash', '-c', "echo ubuntu  hard  nofile  1000000 | tee -a /etc/security/limits.conf"],
        ['sysctl', '-n', '-p'],
    ]
}

def _prepare_user_data():
    '''if cloud-init is enabled, return formatted user-data variable.'''
    if enable_cloud_init:
        return '#cloud-config\n' + yaml.dump(CLOUD_INIT_DATA)
    else:
        return None


def init_cannons():
    """Creates the ec2 instances and returns a list of publicly accessible
    dns names, mapped to each instance.
    """
    ec2_conn = boto.connect_ec2(aws_access_key, aws_secret_key)

    ### Track down an image for our AMI
    images = ec2_conn.get_all_images(ami_key)
    image = images[0]

    ### if cloud-init is enabled, prepare yaml for user-data
    user_data = _prepare_user_data()

    ### Will need unbuffered output
    print 'Deploying cannons...\n',

    ### Display yaml sent to user-data
    if user_data:
        print 'cloud-init configuration sent to EC2 API:\n' + user_data

    ### Create n instances
    try:
        r = image.run(min_count=num_cannons,
                      max_count=num_cannons,
                      placement=placement,
                      security_groups=security_groups,
                      key_name=key_pair_name,
                      instance_type=instance_type,
                      user_data=user_data)
    except boto.exception.EC2ResponseError, e:
        print 'ERROR: Deploy failed: %s' % e
        return

    hosts = []
    running = False
    while not running:
        time.sleep(5)
        [i.update() for i in r.instances]
        status = [i.state for i in r.instances]
        if status.count('running') == len(r.instances):
            running = True
            print 'Done!'
            for i in r.instances:
                if not i.tags:
                    ec2_conn.create_tags([i.id], {'microarmy': '1'})
                hosts.append((i.id, i.public_dns_name))
    print 'Hosts config:', hosts
    return hosts

def find_deployed_cannons():
    """Find all cannons deployed for our purposes"""
    ec2_conn = boto.connect_ec2(aws_access_key, aws_secret_key)

    reservations = ec2_conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]

    hosts = []
    for i in instances:
        if not i.tags:
            continue
        else:
            if 'microarmy' in i.tags and i.state == 'running':
                hosts.append((i.id, i.public_dns_name))

    return hosts

def destroy_deployed_cannons():
    """Find and destroy all our deployed cannons"""
    hosts = find_deployed_cannons()
    terminate_cannons([h[0] for h in hosts])

def terminate_cannons(host_ids):
    """
    """
    ec2_conn = boto.connect_ec2(aws_access_key, aws_secret_key)
    ec2_conn.terminate_instances(host_ids)

def reboot_cannons(host_ids):
    """
    """
    ec2_conn = boto.connect_ec2(aws_access_key, aws_secret_key)
    ec2_conn.reboot_instances(host_ids)

def _setup_a_cannon(hostname):
    """Connects to the hostname and installs all the tools required for the
    load test.

    Returns a boolean for successful setup.
    """
    ssh_conn = ssh_connect(hostname)
    
    # copy script to cannon and make it executable
    script_path = env_scripts_dir + '/' + CANNON_INIT_SCRIPT
    put_file(ssh_conn, script_path, CANNON_INIT_SCRIPT)
    response = exec_command(ssh_conn, 'chmod 755 ~/%s' % CANNON_INIT_SCRIPT)
    if response: # response would be error output
        print 'Unable to chmod cannon script: %s' % (CANNON_INIT_SCRIPT)
        print response
        return False

    # execute the setup script (expect this call to take a while)
    response = exec_command(ssh_conn, 'sudo ./%s' % CANNON_INIT_SCRIPT)
    return (hostname, response)    

def _setup_siege_config(hostname):
    """Connects to the hostname and configures siege

    """
    ssh_conn = ssh_connect(hostname)

    script_path = env_scripts_dir + '/' + SIEGE_CONFIG
    put_file(ssh_conn, script_path, '.siegerc')

def _setup_siege_urls(hostname):
    """Connects to the hostname and configures siege

    """
    ssh_conn = ssh_connect(hostname)

    script_path = env_scripts_dir + '/' + URLS
    put_file(ssh_conn, script_path, 'urls.txt')

def setup_cannons(hostnames):
    """Launches a coroutine to configure each host and waits for them to
    complete before compiling a list of responses
    """
    print '  Loading cannons... ',
    pile = eventlet.GreenPile(pool)
    for h in hostnames:
        pile.spawn(_setup_a_cannon, h)
    responses = list(pile)
    print 'Done!'
    return responses

def setup_siege(hostnames):
    """Launches a coroutine to write a siege config based on user input."""
    print '  Configuring siege... ',
    pile = eventlet.GreenPile(pool)
    for h in hostnames:
        pile.spawn(_setup_siege_config, h)
    responses = list(pile)
    print 'Done!'
    return responses

def setup_siege_urls(hostnames):
    """Launches a coroutine to write siege urls based on user input."""
    print '  Configuring urls... ',
    pile = eventlet.GreenPile(pool)
    for h in hostnames:
        pile.spawn(_setup_siege_urls, h)
    responses = list(pile)
    print 'Done!'
    return responses

def fire_cannon(cannon_host, target):
    """Handles the details of telling a host to fire"""
    ssh_conn = ssh_connect(cannon_host)

    if target:
        remote_command = 'siege --rc /home/ubuntu/.siegerc %s' % (target)
    else:
        remote_command = 'siege --rc /home/ubuntu/.siegerc -f ~/urls.txt'

    # Siege writes stats to stderr
    response = exec_command(ssh_conn, remote_command, return_stderr=True)
    return response

def slam_host(cannon_hosts, target):
    """Coordinates `cannon_hosts` to use the specified siege coordates on
    `target` and report back the performance.
    """
    pile = eventlet.GreenPile(pool)
    for h in cannon_hosts:
        pile.spawn(fire_cannon, h, target)
    responses = list(pile)

    try:
        report = parse_responses(responses)
    except UnparsableData, e:
        return "Unable to parse data properly: %s" % e

    return report

def parse_responses(responses):
    """Quick and dirty."""
    aggregate_dict = {
        'num_trans': [],
        'elapsed': [],
        'tran_rate': [],
    }

    for response in responses:
        try:
            num_trans = response[4].split('\t')[2].strip()[:-5]
            elapsed = response[6].split('\t')[2].strip()[:-5]
            tran_rate = response[9].split('\t')[1].strip()[:-10]
        except IndexError:
            raise UnparsableData(response)

        aggregate_dict['num_trans'].append(num_trans)
        aggregate_dict['elapsed'].append(elapsed)
        aggregate_dict['tran_rate'].append(tran_rate)

    return aggregate_dict
