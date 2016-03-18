########
Mac OS X
########

This tutorial is designed to get a working version os NSoT installed inside a
Mac OS X system. We will install virtual environment wrappers to keep things
tidy, and isolate our installation.

Installation
============

Xcode
-----

It is assumed that you have a Mac, running OS X (written for 10.10.5), and
xcode already installed. If you don't have Xcode, please install it. You may
need to agree to a command line license. We suggest running this via command
line prior to install::

    $ xcodebuild -license

Prerequisites
-------------

We will put our installation of NSoT inside a Python virtual environment to
isolate the installation. To do so we need virtualenv, and virtualenvwrapper.
Open a command prompt, and install them with pip::

    $ pip install virtualenv
    $ pip install virtualenvwrapper

Ensure installation by running a which, and finding out where they now live::
 
    $ which virtualenvwrapper
    $ which virtualenv
 
Next we tell bash where these virtual environments are, and where to save the associated data::

    $ vi ~/.bashrc 
 
Add these three lines::
 
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Devel
    source /usr/local/bin/virtualenvwrapper.sh

Now restart bash to implement the changes::

    $ source ./.bashrc 

Install NSoT
------------

NSoT will be installed via command line, into the folder of your choice. If you
don't have a preffered folder, may we suggest this:: 

    $ mkdir ~/sandbox && cd ~/sandbox
   
Once in the folder of choice, install nsot, and download the repo with git::
 
    $ pip install nsot
    $ git clone https://github.com/dropbox/nsot ./
    
CD into the folder, make a virtual environment, and start it::
   
    $ cd nsot && mkvirtualenv nsot
    $ workon nsot
 
Start the NSoT Demo
===================

Running the demo script will build the database, populate it with test data,
start the proxy, start the service, and begin listening for requests::

    $ demo/run_demo.sh
 
Login to NSoT from a Browser
============================

Once the NSoT server is started, we can login to the system (as
admin@localhost) with the following address: 

http://localhost:8991
