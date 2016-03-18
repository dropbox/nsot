######
Ubuntu
######

This installation guide assumes that you are running Ubuntu version 12.04 or
14.04 on your machine, and are wanting to install NSoT. This guide will help
you install NSoT and then run it locally from a browser window.

Installation
============

To ensure your Ubuntu installation is up to date, please update it. Open a
command prompt and run the following::

    $ sudo apt-get --yes update

Once your machine is up to date, we need to install the latest Python libraries
to facilitate encryption, security, and development tools::

    $ sudo apt-get --yes install build-essential python-dev libffi-dev libssl-dev

The Python Pip installer and the git repository management tools are needed
too. We'll go ahead and get those next:: 

    $ sudo apt-get --yes install python-pip git

Next we'll install NSoT and MrProxy to handle the proxy connections NSoT will
require::

    $ sudo pip install nsot mrproxy

Finally we'll download the NSoT repository, via Git, to the /tmp/nsot
directory::

    $ git clone https://github.com/dropbox/nsot /tmp/nsot

At this point NSoT is installed, the repository should be downloaded, Python
and all dependencies are working, and you can go poke around in the /tmp/nsot
directory.

Debian Permissions
------------------

Ubuntu users may skip this step.

If you are installing NSoT onto a Debian machine you will need to alter the
following permissions::

    $ sudo chown vagrant:vagrant /usr/local/lib/python2.7/dist-packages/
    $ sudo chown vagrant:vagrant /usr/local/include/
    $ sudo chown vagrant:vagrant /usr/local/share/man/

Start NSoT
==========

To Run NSoT, we start the server at the command line::

    $ cd /tmp/nsot/demo      
    $ ./run_demo.sh

The server should come up, and begin listening for requests from the web
browser.

Login Via Web Interface
=======================

Now you may view NSoT from your local browser of your choice. Open the
following URL, which will automatically log you in as the user
``admin@localhost``:

http://192.168.33.11:8991

(Note that you you may need to disable some internal software firewalls to
allow a connection to this virtual machine.)
