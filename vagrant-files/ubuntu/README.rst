##################################
HowTo: NSOT on Vagrant VM w Ubuntu
##################################

The Plan:
=========

Install NSoT on it's own Linux environment: An Ubuntu virtual machine, with Python,
all the dev tools, SSL, etc. We use Vagrant (which requires Oracle's Virtualbox) to
control our virtual machines, and a ``Vagrantfile`` to provision the server from one
file. The ``Vagrantfile`` for Ubuntu can be found in the same directory as this README document.
If you would like to install NSOT on CentOS, please download the Vagrant files for that architecture.

Prerequisite Steps:
To proceed you must have working installations of Vagrant and Virtualbox on your machine. If
you already have these, you may skip this step.

If you do not have a working Vagrant environment configured along with
Virtualbox, please follow the `Getting Started
<https://docs.vagrantup.com/v2/getting-started/>`_ instructions first.

NSOT Vagrant Test Server Instructions
=====================================

1. Download and install this README and associated Vagrantfile to location where you'd like it to run
(5-10 minutes on a fast connection).

----------

2. Provision the virtual machine
Open a command prompt, and run the following:
(5-10 minutes on a fast connection)::
          
    $ cd /{Location of your Vagrantfile}
    $ vagrant up

This will build a new Vagrant box, configure the server, update it, add
software, fix dependencies, ``pip install nsot``, add demo fixtures, and
deploy NSoT.

----------

3. Login to the new virtual machine, cd to demo directory, and run the demo

    $ vagrant ssh
    $ cd /tmp/nsot/demo
    $ ./run_demo.sh

Demo data will be built into the new database, the server will be started, and it will wait for commands
from the web browser in step 4.

----------

4. Open NSoT in your browser

Now you may view NSoT from your local browser of your choice. Open the
following URL, which will automatically log you in as the user
``admin@localhost``:

http://192.168.33.11:8991

(Note that you you may need to disable some internal software firewalls to
allow a connection to this virtual machine.)
