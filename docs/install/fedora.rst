######
Fedora
######

This installation guide assumes that you have installed Fedora 22 on your
machine, and are wanting to install NSoT. This guide will help you install NSoT
and then run it locally from a browser window.

Installation
============

To ensure your Fedora installation is up to date, please update it. 
Once complete, open a command prompt and run the following::

    $ sudo dnf -y install nodejs git gcc gcc-c++ libffi libffi-devel python-devel openssl-devel 
    $ sudo dnf -y gcc-plugin-devel make automake kernel kernel-devel psmisc
    $ sudo dnf -y install python2-devel

Next you'll need to upgrade Pip to the latest version::

    $ sudo pip install --upgrade pip

Now we are ready to Pip install NSoT and MrProxy. MrProxy is there to handle
the proxy connections NSoT will require:: 

    $ sudo pip install nsot mrproxy

Finally we'll download the NSoT repository, via Git, to the /tmp/nsot directory::

    $ git clone https://github.com/dropbox/nsot /tmp/nsot
    $ chown -R vagrant /tmp/nsot

At this point NSoT is installed, the repository should be downloaded, Python
and all dependencies are working, and you can go poke around in the /tmp/nsot
directory.

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
