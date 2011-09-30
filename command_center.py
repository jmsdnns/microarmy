#!/usr/bin/env python


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
import sys

from microarmy.firepower import (init_cannons,
                                 terminate_cannons,
                                 reboot_cannons,
                                 setup_cannons,
                                 slam_host,
                                 setup_siege,
                                 setup_siege_urls)


try:
    from settings import siege_config
except ImportError:
    print 'No siege config detected, continuting...'
    siege_config = None

try:
    from settings import siege_urls
except ImportError:
    print 'No siege urls detected, continuting...'
    siege_urls = None

### Environment info
_cannons_deployed = False
_cannon_hosts = None
_cannon_infos = None

def _write_siege_config(siegerc):

    file_data = None
    return_status = None

    for key, value in siegerc.iteritems():
        if file_data:
            file_data += "%s = %s\n" %(key, value)
        else:
            file_data = "%s = %s\n" %(key, value)

    try:
        siegerc_file = open('./env_scripts/siegerc', 'w')
        siegerc_file.write(file_data)
        siegerc_file.close()
        return_status = True
    except IOError:
        return_status = False

    return return_status

def _write_siege_urls(urls):

    file_data = None
    return_status = None

    for url in urls:
        if file_data:
            file_data += "%s\n" %(url)
        else:
            file_data = "%s\n" %(url)

    try:
        urls_file = open('./env_scripts/urls.txt', 'w')
        urls_file.write(file_data)
        urls_file.close()
        return_status = True
    except IOError:
        return_status = False

    return return_status

### Main command loop
while True:
    try:
        command = raw_input('\nmicroarmy> ')
    except EOFError, KeyboardInterrupt:
        print 'bye'
        sys.exit(0)

    ### Help
    if command == "help":
        print '  help:         This menu.'
        print '  status:       Get info about current cannons'
        print '  deploy:       Deploys N cannons'
        print '  setup:        Runs the setup functions on each host'
        print '  config:       Allows a user to specify existing cannons'
        print '  config_siege: Create siege config from specified dictionary'
        print '  siege_urls:   Specify list of URLS to test against'
        print '  fire:         Asks for a url and then fires the cannons'
        print '  mfire:        Runs `fire` multiple times and aggregates totals'
        print '  term:         Terminate cannons'
        print '  quit:         Exit command center'

    ### Quit
    elif command == "term":
        if not _cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            continue

        terminate_cannons([h[0] for h in _cannon_infos])
        _cannon_infos = None
        _cannon_hosts = None
        _cannons_deployed = False

    ### Exit
    elif command == "quit":
        import sys
        sys.exit(0)

    ### Initialize
    elif command == "deploy":
        _cannon_infos = init_cannons()

    ### Setup cannons
    elif command == "setup":
        if not _cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            continue

        print '  Setting up cannons - time: %s' % (time.time())
        _cannon_hosts = [h[1] for h in _cannon_infos]
        status = setup_cannons(_cannon_hosts)

        if siege_config:
            if _write_siege_config(siege_config):
                print '  Siege config written, deploying to cannons'
                setup_siege(_cannon_hosts)
            else:
                print '  Error writing new siege config'

        if siege_urls:
            if _write_siege_urls(siege_urls):
                print '  Siege urls written, deploying to cannons'
                setup_siege_urls(_cannon_hosts)
            else:
                print '  Error writing urls'

        print '  Finished setup - time: %s' % (time.time())

        print '  Sending reboot message to cannons'
        reboot_cannons([h[0] for h in _cannon_infos])
        _cannons_deployed = True

    ### Siege config
    elif command == "config_siege":
        if _cannons_deployed:
            if siege_config:
                print '  Siege config detected in settings and will be automatically deployed with "setup"'
                answer = raw_input('  Continue? (y/n) ')
                if answer == 'n':
                   continue

            siegerc = raw_input('  Enter siege config data: ')
            if _write_siege_config(eval(siegerc)):
                print '  Siege config written, deploying to cannons'
                setup_siege(_cannon_hosts)
                siege_config = eval(siegerc)
            else:
                print '  Error writing new siege config'
        else:
            print 'ERROR: Cannons not deployed yet'

    elif command == "siege_urls":
        if _cannons_deployed:
            if siege_urls:
                print '  Urls detected in settings and will be automatically deployed with "setup"'
                answer = raw_input('  Continue? (y/n) ')
                if answer == 'n':
                   continue

            siege_urls = raw_input('  Enter urls: ')
            if _write_siege_urls(eval(siege_urls)):
                print '  Urls written, deploying to cannons'
                setup_siege_urls(_cannon_hosts)
                siege_urls = eval(siege_urls)
            else:
                print '  Error writing new urls'
        else:
            print 'ERROR: Cannons not deployed yet'

    ### Status
    elif command == "status":
        if not _cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            continue
        for host in _cannon_infos:
            iid, ihost = [h for h in host]
            print '  Cannon: %s:%s' %(iid, ihost)

        print '\n  Last written siege config: '
        print '  %s' % siege_config

    ### Config
    elif command == "config":
        cannon_data = raw_input('  Enter host data: ')
        _cannon_infos = eval(cannon_data)
        _cannon_hosts = [h[1] for h in _cannon_infos]
        _cannons_deployed = True

    ### Fire
    elif command == "fire":
        if _cannons_deployed:
            if siege_urls:
                report = slam_host(_cannon_hosts, None)
            else:
                target = raw_input('  target: ')
                report = slam_host(_cannon_hosts, target)

            ### Ad-hoc CSV
            print 'Results ]------------------'
            print 'Num_Trans,Elapsed,Tran_Rate'
            total_trans = 0
            for idx in xrange(len(report['num_trans'])):
                total_trans = total_trans + int(report['num_trans'][idx])
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
