#!/usr/bin/env python -u


"""The command center is where assault coordination takes place. A typical use
would be to initialize a bunch of micro instances and use them as siege cannons.

The interface is a prompt offering help and funcitons for building / controlling
the cannons. It is advised you double check the behavior of the system through
Amazon's web interface too.

Access to the cannon's is done via SSH inside eventlet greenpiles.

EC2 console: https://console.aws.amazon.com/ec2/
"""


from eventlet import patcher
patcher.monkey_patch(all=True)

import boto
import time
import datetime

from microarmy.firepower import (init_cannons,
                                 terminate_cannons,
                                 reboot_cannons,
                                 setup_cannons,
                                 slam_host)


### Environment info
_cannons_deployed = False
_cannon_hosts = None
_cannon_infos = None


### Main command loop
while True:
    command = raw_input('\nmicroarmy> ')

    ### Help
    if command == "help":
        print '  help:     This menu.'
        print '  deploy:   Deploys N cannons'
        print '  setup:    Runs the setup functions on each host'
        print '  config:   Allows a user to specify existing cannons'
        print '  fire:     Asks for a url and then fires the cannons'
        print '  mfire:    Runs `fire` multiple times and aggregates totals'
        print '  term:     Terminate cannons'
        print '  quit:     Exit command center'

    ### Quit
    elif command == "term":
        terminate_cannons([h[0] for h in _cannon_infos])

    ### Exit
    elif command == "quit":
        import sys
        sys.exit(0)

    ### Initialize
    elif command == "deploy":
        _cannon_infos = init_cannons()

    ### Setup cannons
    elif command == "setup":
        print '  Setting up cannons - time: %s' % (time.time())
        _cannon_hosts = [h[1] for h in _cannon_infos]
        status = setup_cannons(_cannon_hosts)
        print '  Finished setup - time: %s' % (time.time())

        print '  Sending reboot message to cannons'
        reboot_cannons([h[0] for h in _cannon_infos])
        _cannons_deployed = True

    ### Config
    elif command == "config":
        cannon_data = raw_input('  Enter host data: ')
        _cannon_infos = eval(cannon_data)
        _cannon_hosts = [h[1] for h in _cannon_infos]
        _cannons_deployed = True

    ### Fire
    elif command == "fire":
        if _cannons_deployed:
            target = raw_input('  target: ')
            report = slam_host(_cannon_hosts, target)

            ### Ad-hoc CSV
            print 'Results ]------------------'
            print 'Num_Trans,Elapsed,Tran_Rate'
            total_trans = 0
            for idx in xrange(len(report['num_trans'])):
                total_trans = total_trans + report['num_trans'][idx]
                print '%s,%s,%s' % (report['num_trans'][idx],
                                    report['elapsed'][idx],
                                    report['tran_rate'][idx])
            print 'Total:', total_trans
        else:
            print 'ERROR: Cannons not deployed yet'

    ### MultiFire
    elif command == "mfire":
        if _cannons_deployed:
            ### Get test arguments from user
            try:
                target =  raw_input('   target: ')
                n_times = raw_input('  n times: ')
                n_times = int(n_times)
            except:
                print '<target> must be a string.'
                print '<n_times> must be a number.'
                raise

            print 'Results ]------------------'
            print 'Run ID,Sum Transactions,Sum Transaction Rate'
            total_transactions = 0
            for run_instance in xrange(n_times):
                report = slam_host(_cannon_hosts, target)

                ### Ad-hoc CSV
                sum_num_trans = 0.0
                sum_tran_rate = 0.0
                for idx in xrange(len(report['num_trans'])):
                    sum_num_trans = sum_num_trans + float(report['num_trans'][idx])
                    sum_tran_rate = sum_tran_rate + float(report['tran_rate'][idx])

                total_transactions = total_transactions + sum_num_trans
                print '%s,%s,%s' % (run_instance, sum_num_trans, sum_tran_rate)
            print 'Total:', total_transactions
        else:
            print 'ERROR: Cannons not deployed yet'
