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


## Slides

I gave a talk on Micro Army back in May of 2011. The slides are available
(here)[http://j2labs.tumblr.com/post/5823446661/micro-army-slides-from-my-talk].


## 100 boxes in parallel

I recently tested deployment of 100 ec2 micros.  On average I found I was able
to turn configure 2 micros in about 58 seconds.  I tried configuring 100 micros
in parallel and found this only took 106 seconds.  Slightly more, but negligibly
so.


## Example Use:

This is what it looks like to use microarmy.

    $ ./command_center.py

    microarmy> long_help

      long_help:    This.
      status:       Get info about current cannons
      deploy:       Deploys N cannons
      setup:        Runs the setup functions on each host
      config:       Allows a user to specify existing cannons
      config_siege: Create siege config from specified dictionary
      siege_urls:   Specify list of URLS to test against
      single_url:   Only hit one url when firing off your next test
      all_urls:     Revert to using configured urls (turns off single_url)
      fire:         Asks for a url and then fires the cannons
      mfire:        Runs `fire` multiple times and aggregates totals
      term:         Terminate cannons
      quit:         Exit command center

    microarmy> deploy
    Deploying cannons...  Done!
    Hosts config: [(u'i-4c4ff03c', u'ec2-107-21-75-120.compute-1.amazonaws.com'), (u'i-4e4ff03e', u'ec2-50-42-133-31.compute-1.amazonaws.com')]

    microarmy> setup
      Setting up cannons - time: 1317352247.23
      Loading cannons...  Done!
      Siege config written, deploying to cannons
      Configuring siege...  Done!
      Siege urls written, deploying to cannons
      Configuring urls...  Done!
      Finished setup - time: 1317352305.56
      Sending reboot message to cannons

    microarmy> fire
      target: http://brubeck.io
    Results ]------------------
    Num_Trans,Elapsed,Tran_Rate
    3424,9.15,374.21
    3424,9.17,373.39

    microarmy> term

    microarmy> quit

## Configure siege dynamically

Typically you'd want to configure the siege config in your `local_settings.py` like so...

    siege_config = {
        'connection': 'close',
        'concurrency': 5,
        'internet': 'true'
    }

If you wish to configure it dynamically...

    microarmy> config_siege
      Siege config detected in settings and will be automatically deployed with "setup"
      Continue? (y/n) y
      Enter siege config data: {'connection': 'close', 'concurrency': 5, 'benchmark': 'true'}
      Siege config written, deploying to cannons
      Configuring siege...  Done!

All of the above will write a `~/.siegerc` config on the cannon machines like so:

    connection = close
    benchmark = true
    concurrency = 5

## Configure siege urls

Typically you'd want to configure the urls for siege to hit in your `local_settings.py` like so:

    siege_urls = [
       'http://localhost/',
       'http://localhost/test'
    ]

If you wish to configure them dynamically...

    microarmy> siege_urls
      Urls detected in settings and will be automatically deployed with "setup"
      Continue? (y/n) y
      Enter urls: ['http://localhost/', 'http://localhost/test/']
      Urls written, deploying to cannons
      Configuring urls...  Done!

All of the above will write `~/urls.txt` on the cannon machines like so:

    http://localhost/
    http://localhost/test/

## Hit a single url target instead of the configured list

You might want to hit one single url when firing off a test, to do so, don't configure any urls in your `local_settings.py` or...

    microarmy> single_url
      Bypassing configured urls
    microarmy> fire
      target: http://localhost/test_one/

To switch back to your configured urls...

    microarmy> all_urls
      Using configured urls

## Find and reuse previously deployed cannons

Sometimes you might forget that you deployed a whole mess of cannons already. In that case, run the following...

    microarmy> find_cannons
    Deployed cannons: [(u'i-1a6d127a', u'ec2-50-17-80-241.compute-1.amazonaws.com'), (u'i-1c6d127c', u'ec2-184-73-117-126.compute-1.amazonaws.com'), (u'i-e06d1280', u'ec2-50-16-106-209.compute-1.amazonaws.com'), (u'i-e26d1282', u'ec2-50-17-26-28.compute-1.amazonaws.com'), (u'i-e46d1284', u'ec2-50-16-169-72.compute-1.amazonaws.com'), (u'i-e66d1286', u'ec2-184-73-114-245.compute-1.amazonaws.com'), (u'i-e86d1288', u'ec2-184-72-92-234.compute-1.amazonaws.com'), (u'i-ea6d128a', u'ec2-184-73-148-253.compute-1.amazonaws.com'), (u'i-ec6d128c', u'ec2-107-20-112-149.compute-1.amazonaws.com'), (u'i-ee6d128e', u'ec2-50-16-24-210.compute-1.amazonaws.com'), (u'i-f06d1290', u'ec2-204-236-251-120.compute-1.amazonaws.com'), (u'i-f46d1294', u'ec2-50-19-24-63.compute-1.amazonaws.com'), (u'i-f66d1296', u'ec2-107-20-95-203.compute-1.amazonaws.com'), (u'i-f86d1298', u'ec2-174-129-76-108.compute-1.amazonaws.com'), (u'i-fa6d129a', u'ec2-50-16-64-128.compute-1.amazonaws.com')]
    Would you like to import these cannons now? (y/n) y

Now you have a whole new battery of cannons to fire away. To be safe, you may want to run `setup` again.

## Terminate all cannons we know about

Thanks to tagging instances in EC2, we can get an inventory of all the cannons we've deployed over time.
That's good because you don't want to leave those little beasts running.

If you're all done and want to be sure your instances are terminated, do the following...

    microarmy> find_cannons
    Deployed cannons: [(u'i-1a6d127a', u'ec2-50-17-80-241.compute-1.amazonaws.com'), (u'i-1c6d127c', u'ec2-184-73-117-126.compute-1.amazonaws.com'), (u'i-e06d1280', u'ec2-50-16-106-209.compute-1.amazonaws.com'), (u'i-e26d1282', u'ec2-50-17-26-28.compute-1.amazonaws.com'), (u'i-e46d1284', u'ec2-50-16-169-72.compute-1.amazonaws.com'), (u'i-e66d1286', u'ec2-184-73-114-245.compute-1.amazonaws.com'), (u'i-e86d1288', u'ec2-184-72-92-234.compute-1.amazonaws.com'), (u'i-ea6d128a', u'ec2-184-73-148-253.compute-1.amazonaws.com'), (u'i-ec6d128c', u'ec2-107-20-112-149.compute-1.amazonaws.com'), (u'i-ee6d128e', u'ec2-50-16-24-210.compute-1.amazonaws.com'), (u'i-f06d1290', u'ec2-204-236-251-120.compute-1.amazonaws.com'), (u'i-f46d1294', u'ec2-50-19-24-63.compute-1.amazonaws.com'), (u'i-f66d1296', u'ec2-107-20-95-203.compute-1.amazonaws.com'), (u'i-f86d1298', u'ec2-174-129-76-108.compute-1.amazonaws.com'), (u'i-fa6d129a', u'ec2-50-16-64-128.compute-1.amazonaws.com')]
    Would you like to import these cannons now? (y/n) y
    microarmy> cleanup
    Deployed cannons destroyed


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
    siege_config = {
        'connection': 'close',
        'concurrency': 5,
        'internet': 'true'
    }

    siege_urls = [
       'http://localhost/',
       'http://localhost/test'
    ]
