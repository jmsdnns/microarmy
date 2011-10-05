#!/usr/bin/env python


"""The command center is where assault coordination takes place. A typical use
would be to initialize a bunch of micro instances and use them as siege cannons.

The interface is a prompt offering help and funcitons for building / controlling
the cannons. It is advised you double check the behavior of the system through
Amazon's web interface too.

Access to the cannon's is done via SSH inside eventlet greenpiles.

EC2 console: https://console.aws.amazon.com/ec2/
"""

import cmd
from microarmy.commands import CommandCenter
import sys

if __name__ == '__main__':
    try:
        CommandCenter().cmdloop()
    except KeyboardInterrupt:
       print 'bye'
       sys.exit(0)

