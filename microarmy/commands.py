"""Command dispatcher and commands to run.

Look up the command from the command center, attempt to map it to a local method.

"""

from eventlet import patcher
patcher.monkey_patch(all=True)

import boto
import time
import datetime
import sys
import cmd

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
    from settings import siege_config as _siege_config
except ImportError:
    print 'No siege config detected, continuting...'
    _siege_config = None

try:
    from settings import siege_urls as _siege_urls
except ImportError:
    print 'No siege urls detected, continuting...'
    _siege_urls = None


class Commands(object):
    """Commands and helpers for command center."""

    def __init__(self):
        self._cannons_deployed = False
        self._cannon_hosts = None
        self._cannon_infos = None
        self._bypass_urls = False
        self._siege_urls = _siege_urls
        self._siege_config = _siege_config

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

    def do_deploy(self, line):
        """Deploy N cannons"""
        start_time = time.time()
        self._cannon_infos = init_cannons()
        print 'Time: %s' %(time.time()-start_time)

    def do_term(self, line):
        """Terminate cannons"""
        if not self._cannon_infos:
            print 'No cannons defined, try "config" or "deploy"'
            return

        terminate_cannons([h[0] for h in self._cannon_infos])
        self._cannon_infos = None
        self._cannon_hosts = None
        self._cannons_deployed = False
        print 'Deployed cannons destroyed'

    def do_quit(self, line):
        """Exit command center"""
        print 'bye'
        sys.exit(0)

    def do_setup(self, line):
        """Setup system, deploy configs and urls"""
        if not self._cannon_infos:
            print '  No cannons defined, try "config" or "deploy"'
            return

        start_time = time.time()
        print '  Setting up cannons'
        self._cannon_hosts = [h[1] for h in self._cannon_infos]
        status = setup_cannons(self._cannon_hosts)

        if self._siege_config:
            if self._write_siege_config(self._siege_config):
                print '  Siege config written, deploying to cannons'
                setup_siege(self._cannon_hosts)
            else:
                print '  Error writing new siege config'

        if self._siege_urls:
            if self._write_siege_urls(self._siege_urls):
                print '  Siege urls written, deploying to cannons'
                setup_siege_urls(self._cannon_hosts)
            else:
                print '  Error writing urls'

        print '  Finished setup - time: %s' % (time.time()-start_time)

        print '  Sending reboot message to cannons'
        reboot_cannons([h[0] for h in self._cannon_infos])
        self._cannons_deployed = True

    def do_config_siege(self, line):
        """Create siege config, deploy it to cannons"""
        if self._cannons_deployed:
            if self._siege_config:
                print '  Siege config detected in settings and will be automatically deployed with "setup"'
                answer = raw_input('  Continue? (y/n) ')
                if answer.lower() == 'n':
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

    def do_siege_urls(self, line):
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

    def do_single_url(self, line):
        """Bypass configured urls, allowing to specify one dynamically"""
        self._bypass_urls = True
        print '  Bypassing configured urls'

    def do_all_urls(self, line):
        """Disable 'single_url' mode"""
        self._bypass_urls = False
        print '  Using configured urls'

    def do_status(self, line):
        """Get information about current cannons, siege configs and urls"""
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

    def do_config(self, line, cannon_data=None):
        """Allows a user to specify existing cannons"""
        if not cannon_data:
            cannon_data = raw_input('  Enter host data: ')
        if cannon_data != '':
            if isinstance(cannon_data, str):
                self._cannon_infos = eval(cannon_data)
            else:
                self._cannon_infos = cannon_data
            self._cannon_hosts = [h[1] for h in self._cannon_infos]
            self._cannons_deployed = True
        else:
            print 'ERROR: No host data specified'
        return

    def do_find_cannons(self, line):
        """Find all cannons deployed for microarmy"""
        hosts = find_deployed_cannons()
        if hosts:
            print 'Deployed cannons:', hosts
            answer = raw_input('  Would you like to import these cannons now? (y/n) ')
            if answer.lower() == 'n':
                return
            self.do_config(None, hosts)
        else:
            print 'No cannons found'

    def do_cleanup(self, line):
        """Find all cannons we have deployed, destroy them all"""
        destroy_deployed_cannons()
        print '  Deployed cannons destroyed'

    def do_fire(self, line):
        """Fires the cannons, asks for URL if none are defined in settings"""
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

    def do_mfire(self, line):
        """Runs `fire` multiple times and aggregates totals"""
        if self._cannons_deployed:
            ### Get test arguments from user
            try:

                if not self._siege_urls and self._bypass_urls:
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


class CommandCenter(cmd.Cmd, Commands):
    """Simple command center shell.
    "Mixes in" commands in Commands for dispatch.
    Should probably actually write a mixin.
    """

    prompt = 'microarmy> '

    def __init__(self):
        Commands.__init__(self)
        super(CommandCenter, self).__init__()

    def default(self, line):
        print
        print 'Cannot find command: "%s"' % line
        self.do_help(None)

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print 'bye'
        return True
