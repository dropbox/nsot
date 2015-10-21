###################################
NSoT on CentOS Install Instructions 
###################################

This installation guide assumes that you have installed CentOS 12.4 on your machine, and are wanting to install NSoT.
This guide will help you install NSoT and then run it locally from a browser window.


1. Install Python, Dependencies, PIP, and NSOT
==============================================

To ensure your CentOS installation is up to date, please update it. 
Once complete, open a command prompt and run the following::

    $ sudo yum install -y   nodejs mod_ssl openssl git
    $ sudo yum install -y   python-devel
    $ sudo yum install -y  libffi-devel openssl-devel
    $ sudo yum install -y  epel-release
    $ sudo yum install -y  python-pip
          

Next you'll need to upgrade Pip to the latest version::

    $ sudo pip install --upgrade pip

To complete the prerequisites, we'll need some more Python Compilers and dev tool::

    $ sudo yum install -y  gcc-plugin-devel python-devel
    $ sudo pip install requests[security]

Now we are ready to Pip install NSoT and MrProxy. MrProxy is there to handle the proxy connections NSoT will require::

    $ sudo pip install nsot mrproxy

Finally we'll download the NSoT repository, via Git, to the /tmp/nsot directory::

    $ git clone https://github.com/dropbox/nsot /tmp/nsot

At this point NSoT is installed, the repository should be downloaded, Python and all dependencies are
working, and you can go poke around in the /tmp/nsot directory.

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
