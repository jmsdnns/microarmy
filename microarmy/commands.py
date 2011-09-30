"""Command dispatcher and commands to run.

Look up the command from the command center, attempt to map it to a local method.

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
                                 setup_siege_urls,
                                 find_deployed_cannons,
                                 destroy_deployed_cannons)

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


class CommandRunner(object):
    """Command runner and commands."""

    def __init__(self):
        self._cannons_deployed = False
        self._cannon_hosts = None
        self._cannon_infos = None
        self._bypass_urls = False
        self._siege_urls = siege_urls
        self._siege_config = siege_config

    def dispatch_command(self, command):
        """Try to map incoming command to local method"""

        if hasattr(self, '_' + command):
            return_command = getattr(self, '_' + command)
            return_command()
        else:
            print
            print '  Cannot find command "%s"' % command
            self._help()

    def _write_siege_config(self, siegerc):
        """Write siege config to local disk before deploying"""

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

    def _write_siege_urls(self, urls):
        """Write siege urls to local disk before deploying"""

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

    def _help(self):
        """Print out help commands"""

        print
        print '  help:         This menu.'
        print '  status:       Get info about current cannons'
        print '  deploy:       Deploys N cannons'
        print '  setup:        Runs the setup functions on each host'
        print '  config:       Allows a user to specify existing cannons'
        print '  find_cannons: Find all cannons deployed for microarmy'
        print '  cleanup:      Find all cannons we have deployed, destroy them all'
        print '  config_siege: Create siege config from specified dictionary'
        print '  siege_urls:   Specify list of URLS to test against'
        print '  single_url:   Only hit one url when firing off your next test'
        print '  all_urls:     Revert to using configured urls (turns off single_url)'
        print '  fire:         Asks for a url and then fires the cannons'
        print '  mfire:        Runs `fire` multiple times and aggregates totals'
        print '  term:         Terminate cannons'
        print '  quit:         Exit command center'

    def _deploy(self):
        """Create new EC2 instances"""

        self._cannon_infos = init_cannons()

    def _term(self):
        """Destroy EC2 instances"""

        if not self._cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            return

        terminate_cannons([h[0] for h in self._cannon_infos])
        self._cannon_infos = None
        self._cannon_hosts = None
        self._cannons_deployed = False
        print '  Deployed cannons destroyed'

    def _quit(self):
        """Leave the shell"""

        import sys
        sys.exit(0)

    def _setup(self):
        """Setup system, deploy configs and urls"""

        if not self._cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            return

        print '  Setting up cannons - time: %s' % (time.time())
        self._cannon_hosts = [h[1] for h in self._cannon_infos]
        status = setup_cannons(self._cannon_hosts)

        if self._siege_config:
            if self._write_siege_config(self._siege_config):
                print '  Siege config written, deploying to cannons'
                setup_siege(self._cannon_hosts)
            else:
                print '  Error writing new siege config'

        if siege_urls:
            if self._write_siege_urls(siege_urls):
                print '  Siege urls written, deploying to cannons'
                setup_siege_urls(self._cannon_hosts)
            else:
                print '  Error writing urls'

        print '  Finished setup - time: %s' % (time.time())

        print '  Sending reboot message to cannons'
        reboot_cannons([h[0] for h in self._cannon_infos])
        self._cannons_deployed = True

    def _config_siege(self):
        """Create siege config, deploy it to cannons"""

        if self._cannons_deployed:
            if self._siege_config:
                print '  Siege config detected in settings and will be automatically deployed with "setup"'
                answer = raw_input('  Continue? (y/n) ')
                if answer == 'n':
                   return

            siegerc = raw_input('  Enter siege config data: ')
            if self._write_siege_config(eval(siegerc)):
                print '  Siege config written, deploying to cannons'
                setup_siege(self._cannon_hosts)
                self._siege_config = eval(siegerc)
            else:
                print '  Error writing new siege config'
        else:
            print 'ERROR: Cannons not deployed yet'

    def _siege_urls(self):
        """Create siege urls file, deploy it to cannons"""

        if self._cannons_deployed:
            if self._siege_urls:
                print '  Urls detected in settings and will be automatically deployed with "setup"'
                answer = raw_input('  Continue? (y/n) ')
                if answer == 'n':
                   return

            siege_urls = raw_input('  Enter urls: ')
            if self._write_siege_urls(eval(siege_urls)):
                print '  Urls written, deploying to cannons'
                setup_siege_urls(self._cannon_hosts)
                self._siege_urls = eval(siege_urls)
            else:
                print '  Error writing new urls'
        else:
            print 'ERROR: Cannons not deployed yet'

    def _single_url(self):
        """Bypass configured urls, allowing to specify one dynamically"""

        self._bypass_urls = True
        print '  Bypassing configured urls'

    def _all_urls(self):
        """Revert bypassing configured urls"""

        self._bypass_urls = False
        print '  Using configured urls'

    def _status(self):
        """Get current status"""

        if not self._cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            return
        for host in self._cannon_infos:
            iid, ihost = [h for h in host]
            print '  Cannon: %s:%s' %(iid, ihost)

        print '\n  Last written siege config: '
        print '  %s' % self._siege_config

        print '\n  Last written urls: '
        print '  %s' % self._siege_urls

    def _config(self):
        """Dynamically configure host data"""

        cannon_data = raw_input('  Enter host data: ')
        if cannon_data != '':
            self._cannon_infos = eval(cannon_data)
            self._cannon_hosts = [h[1] for h in self._cannon_infos]
            self._cannons_deployed = True
        else:
            print '  No host data specified'
        return

    def _find_cannons(self):
        """Find all cannons deployed for our purposes"""
        hosts = find_deployed_cannons()
        if hosts:
            print '  Deployed cannons:', hosts
        else:
            print '  No cannons found'

    def _cleanup(self):
        """Find all cannons deployed for us, wipe those bitches out"""
        destroy_deployed_cannons()
        print '  Deployed cannons destroyed'

    def _fire(self):
        """FIRE ZE CANNONS"""

        if self._cannons_deployed:
            if self._siege_urls and not self._bypass_urls:
                report = slam_host(self._cannon_hosts, None)
            else:
                target = raw_input('  target: ')
                if target != '':
                    report = slam_host(self._cannon_hosts, target)
                else:
                    print '  No target specified'
                    return

            if isinstance(report, str):
                print report
                return

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

    def _mfire(self):
        """FIRE ZE CANNONS LOTS OF TIEMS"""

        if self._cannons_deployed:
            ### Get test arguments from user
            try:
                target =  raw_input('   target: ')
                n_times = raw_input('  n times: ')
                n_times = int(n_times)
            except:
                print '<target> must be a string.'
                print '<n_times> must be a number.'
                return

            print 'Results ]------------------'
            print 'Run ID,Sum Transactions,Sum Transaction Rate'
            total_transactions = 0
            for run_instance in xrange(n_times):
                report = slam_host(self._cannon_hosts, target)

                if isinstance(report, str):
                    print report
                    return

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
