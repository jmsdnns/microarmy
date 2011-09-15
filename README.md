# Micro Army

This is a tool to quickly turn on some number of AWS micro instances and have 
them slam a webserver simultaneously. The micro's are effectively
[Siege](http://www.joedog.org/index/siege-home) cannons.

Siege is a flexible load testing tool. You can configure different payloads and
frequencies and all kinds of good stuff. So the trick for microarmy is to get
Siege on a bunch of computers quickly and coordinate the micro instances to work
in parallel.

The micro instances are controlled via SSH in parallel thanks to Eventlet +
Paramiko.

The micros report the statistics of their run back to the controlling script,
which then aggregates this data into a CSV.

After running the test you can shut down all of your micros and quit micro army.


## 100 boxes in parallel

I recently tested deployment of 100 ec2 micros.  On average I found I was able
to turn configure 2 micros in about 58 seconds.  I tried configuring 100 micros
in parallel and found this only took 106 seconds.  Slightly more, but negligibly
so.


## Example Use:

This is what it looks like to use microarmy.

    $ ./command_center.py 

    microarmy> help
      help:     This menu.
      deploy:   Deploys N cannons
      setup:    Runs the setup functions on each host
      config:   Allows a user to specify existing cannons
      fire:     Asks for a url and then fires the cannons
      term:     Terminate cannons
      quit:     Exit command center

    microarmy> deploy
    Deploying cannons...  Done!
    Hosts config: [(u'i-4c4ff03c', u'ec2-107-21-75-120.compute-1.amazonaws.com'), (u'i-4e4ff03e', u'ec2-50-42-133-31.compute-1.amazonaws.com')]
    
    microarmy> setup
      Setting up cannons - time: 1316054017.06
      Loading cannons...  Done!
      Finished setup - time: 1316054069.83

    microarmy> fire
      target: http://brubeck.io
    Results ]------------------
    Num_Trans,Elapsed,Tran_Rate
    3424,9.15,374.21
    3424,9.17,373.39

    microarmy> term
    
    microarmy> quit
    

## Requirements

There are only a few requirements. Everything required for the micros is
installed on the micros, after all.

    $ pip install eventlet paramiko boto
    

## Config

You should create a `local_settings.py` inside the repo and fill in the
following keys. Look at `settings.py` for more information.

* aws_access_key
* aws_secret_key
* security_groups
* key_pair_name
* num_cannons
* ec2_ssh_key

Here is an example:
                     
    aws_access_key = 'ABCDEFGHIJKLMNOPQRST'
    aws_secret_key = 'abcdefghij/KLMNOPQRSTUVWXY/zabcdefghijkl'
    security_groups = ['MicroArmy'] # must support incoming SSH + outgoing HTTP
    key_pair_name = 'micros'
    ec2_ssh_key = '/Users/jd/.ec2/micros.pem'
    num_cannons = 2
