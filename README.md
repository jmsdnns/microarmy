# Micro Army

This is a tool to quickly turn on some number of AWS micro instances and have them slam a webserver simultaneously, using (Siege)[http://www.joedog.org/index/siege-home].

Siege is a flexible load testing tool. You can configure different payloads and frequencies and all kinds of good stuff. So the trick for microarmy is to get Siege on a bunch of computers quickly and coordinate the micro instances to work in parallel. The micro instances are controlled via SSH in parallel, thanks to Eventlet + Paramiko.

After the micro's have finished, the output from each Siege instance is parsed to produce a CSV report.

## Example Use:

Here is roughly using micro army looks like.

    $ ./command_center.py 
    command :: help
      help:     This menu.
      quit:     RIP
      deploy:   Starts cannon initializations routines
      fire:     Asks for a url and then fires the cannons
    command :: deploy
    Deploying cannons...  Done!
    0|r-2099994d|ec2-55-16-57-191.compute-1.amazonaws.com|ip-10-19-198-177.ec2.internal
    1|r-2099994d|ec2-58-17-30-12.compute-1.amazonaws.com|ip-10-194-19-74.ec2.internal
    2|r-2099994d|ec2-53-13-175-166.compute-1.amazonaws.com|ip-10-19-63-20.ec2.internal
    Giving cannons 30 seconds to boot
    Loading cannons...    Done!
    command :: fire
      target: 'http://webserver' 
    REPORT ]-------------------
    Num_Trans,Elapsed,Tran_Rate
    3679,9.54,385.64
    3635,9.48,383.29
    3535,9.33,378.89

## Requirements

There are only a few requirements.

1. [eventlet](http://eventlet.net/)
2. [paramiko](http://www.lag.net/paramiko/)
3. [boto](http://boto.cloudhackers.com/)


    $ pip install eventlet paramiko boto

## Config

You should create a local_settings.py inside the repo and fill in the following
keys. Look at `settings.py` for more information.

* aws_access_key
* aws_secret_key
* security_groups
* key_pair_name
* num_cannons
* ec2_ssh_key

