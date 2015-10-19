##############################
Install Options & Instructions
##############################


.. toctree::
   :titlesonly:
   NSoT*
   nsot*

Network Server of Truth, or NSoT, is designed to run on multiple architectures and environments that support Python.
Provided the host is properly configured, NSoT can be installed with a single command line entry.::

    $ pip install nsot

However, we undand not all machines are already configured for NSoT. Below we have outlined instructions for 
clean distro installs, Vagrantfiles for single file Virtual Server installations, and instructions for isolating 
NSoT inside Mac OS X.  

1. Install NSoT into clean Ubuntu 12 Distro:
============================================
NSoT runs well inside Ubuntu servers, and is considered front line stable.
Assuming you have just installed Ubuntu 12.* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-Ubuntu-Install`

2. Install NSoT into clean CentOS Distro:
=========================================
NSoT runs well inside CentOS servers, and is considered front line stable.
Assuming you have just installed CentOS 12.* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-CentOS-Install`


3. NSoT in Python Virtual Environment on Mac (local)
====================================================
NSoT can be installed natively onto any Mac OS X that has python. However we reccomend putting the install into 
a virtual environment, isolating the install of python, and a few other tweaks to make sure your install runs smoothly.

--coming soon...


4. Vagrant Virtual Servers inside Mac OSX
=========================================
NSoT is available via Vagrantfile. A single Vagrantfile builds a distribution server, installs the prerequisites, python,
pip, and finally installs NSoT via the vagrant system.  This system, once configured, helps you to start a server like Ubuntu, with a single command. Once Ubuntu is started, you login, and Start the NSoT server. 
When you are done, you can destroy your vagrant server, and all of it`s trimmings, with one command.
This is a great way for beginners and experts to try NSoT in different environments.


CentOS Vagrantfile
------------------
    :doc:`/nsot-centos-vagrant`

Ubuntu 12.4 Vagrantfile
-----------------------
    :doc:`/nsot-ubuntu-vagrant`

