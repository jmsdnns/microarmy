# Micro Army

This is a tool for deploying lots of ec2 micro's, loading siege on them, and
coordinating a load test on webservers. 

It then parses the Siege output to return something like a CSV.

## Example Use:

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
    Num_Trans,Elapsed,Tran_Rate
    3679,9.54,385.64
    3635,9.48,383.29
    3535,9.33,378.89

## Requirements

There are only a few requirements.

1. eventlet
2. paramiko
3. boto

