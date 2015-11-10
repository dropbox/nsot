###################################
NSoT on SuSe Install Instructions 
###################################

This installation guide assumes that you have installed SuSe 13 on your machine, and are wanting to install NSoT.
This guide will help you install NSoT and then run it locally from a browser window.


1. Install Python, Dependencies, PIP, and NSOT
==============================================

To ensure your SuSe installation is up to date, please update it.
We'll begin by opening a command prompt. Make sure your certificates are properly installed, or use this certificate::

    $ wget --no-check-certificate 'https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub' -O /home/vagrant/.ssh/authorized_keys

Now we'll install the prerequisite software with zypper:: 

    $ sudo zypper --non-interactive in nodejs nodejs-devel
    $ sudo zypper --non-interactive in python-devel gcc gcc-c++ git libffi48-devel libopenssl-devel python-pip 

Next you'll need to upgrade Pip and add some features::

    $ sudo pip install --upgrade pip
    $ sudo pip install requests[security]

Now we are ready to Pip install NSoT and MrProxy. MrProxy is there to handle the proxy connections NSoT will require::

    $ sudo pip install nsot mrproxy

Finally we'll download the NSoT repository, via Git, to the /tmp/nsot directory::

    $ git clone https://github.com/dropbox/nsot /tmp/nsot

At this point NSoT is installed, the repository should be downloaded, Python and all dependencies are
working, and you can go poke around in the /tmp/nsot directory.

SuSe Firewall:
--------------
To access NSoT from a local browser we'll need to turn off the security for this demo::

    $  sudo /sbin/service SuSEfirewall2_setup stop 

For production installations we reccomend adding a rule to your iptables for NSoT on ports 8990 and 8991.

2. Start NSoT
=============

To Run NSoT, we start the server at the command line::

    $ cd /tmp/nsot/demo
    $ ./run_demo.sh

The server should come up, and begin listening for requests from the web browser.

3. Login Via Web Interface
==========================

Now you may view NSoT from your local browser of your choice. Open the
following URL, which will automatically log you in as the user
``admin@localhost``:

http://192.168.33.11:8991

(Note that you you may need to disable some internal software firewalls to
allow a connection to this virtual machine.)
