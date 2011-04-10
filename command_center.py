#!/usr/bin/env python -u

"""The command center is where assault coordination takes place. A typical use
would be to initialize a bunch of micro instances and use them as siege cannons.

The cannons then open a zeromq socket and wait for instructions from the command
center. A JSON message is sent that tells the siege configuration to use and the
siege output is sent back to the command center for processing / aggregation.

The interface is a prompt offering help and funcitons for building / controlling
the cannons. It is advised you double check the behavior of the system through
Amazon's web interface too.

EC2 console: https://console.aws.amazon.com/ec2/
"""

from eventlet import patcher
patcher.monkey_patch(all=True)

import boto
import time

from microarmy.firepower import init_cannons, setup_cannons, slam_host

_cannons_deployed = False
_cannon_hosts = None
while True:
    command = raw_input('command :: ')

    ## HELP
    if command == "help":
        print '  help:     This menu.'
        print '  quit:     RIP'
        print '  deploy:   Starts cannon initializations routines'
        print '  config:   Allows a user to specify existing cannons'
        print '  fire:     Asks for a url and then fires the cannons'      

    ## QUIT
    elif command == "quit":
        import sys
        sys.exit(0)

    ## INIT_CANNONS
    elif command == "deploy":
        _cannon_hosts = init_cannons()
        print 'Giving cannons 30 seconds to boot'
        time.sleep(30)
        status = setup_cannons(_cannon_hosts)
        _cannons_deployed = True

    # CONFIG
    elif command == "config":
        host_string = raw_input('  type host list: ')
        hosts = eval(host_string)
        _cannon_hosts = hosts
        _cannons_deployed = True

    # FIRE
    elif command == "fire":
        if _cannons_deployed:
            target = raw_input('  target: ')
            report = slam_host(_cannon_hosts, target)

            # *close* to a CSV
            print 'Results ]------------------'
            print 'Num_Trans,Elapsed,Tran_Rate'
            for idx in xrange(len(report['num_trans'])):
                print '%s,%s,%s' % (report['num_trans'][idx],
                                    report['elapsed'][idx],
                                    report['tran_rate'][idx])
        else:
            print 'ERROR: Cannons not deployed yet'
        

