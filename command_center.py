#!/usr/bin/env python


"""The command center is where assault coordination takes place. A typical use
would be to initialize a bunch of micro instances and use them as siege cannons.

The interface is a prompt offering help and funcitons for building / controlling
the cannons. It is advised you double check the behavior of the system through
Amazon's web interface too.

Access to the cannon's is done via SSH inside eventlet greenpiles.

EC2 console: https://console.aws.amazon.com/ec2/
"""

from microarmy.commands import CommandRunner
import sys

commands = CommandRunner()

while True:
    try:
        command = raw_input('\nmicroarmy> ')
        commands.dispatch_command(command)
    except (EOFError, KeyboardInterrupt):
        print 'bye'
        sys.exit(0)

