import paramiko
import os

from settings import (
    ec2_ssh_key,
    ec2_ssh_username,
)

###
### SSH funcitons
###

def ssh_connect(host, port=22):
    """Helper function to initiate an ssh connection to a host."""
    transport = paramiko.Transport((host, port))
    
    if os.path.exists(ec2_ssh_key):
        rsa_key = paramiko.RSAKey.from_private_key_file(ec2_ssh_key)
        transport.connect(username=ec2_ssh_username, pkey=rsa_key)
    else:
        raise TypeError("Incorrect private key path")
    
    return transport

def sftp_connect(transport):
    """Helper function to create an SFTP connection from an SSH connection.

    Once a connection is established, a user can use conn.get(remotepath)
    or conn.put(localpath, remotepath) to transfer files.
    """
    return paramiko.SFTPClient.from_transport(transport)

def exec_command(transport, command, return_stderr=False):
    """Executes a command on the same server as the provided transport.
    Returns (True, ...) for success and (False, ...) for failure.
    """
    channel = transport.open_session()
    channel.exec_command(command)
    output = channel.makefile('rb', -1).readlines()
    if not return_stderr and output:
        return output
    else:
        return channel.makefile_stderr('rb', -1).readlines()

def put_file(transport, local_path, remote_path):
    """Short hand for transmitting a single file"""
    return put_files(transport, [(local_path, remote_path)])

def put_files(transport, paths):
    """Paths is expected to be a list of 2-tuples. The first element is the
    local filepath. Second is the remote path, eg. where you're putting the
    file.

        paths = [('local_file.py', '/var/www/web/local_file.py'),
                 ('/some/where/is/a/file.html', '/var/www/web/file.html')]
    """
    sftp_conn = sftp_connect(transport)
    for (local,remote) in paths:
        sftp_conn.put(local, remote)
    sftp_conn.close()

