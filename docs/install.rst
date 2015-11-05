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

However, we understand not all machines are already configured for NSoT. Below we have outlined instructions for 
clean distro installs, Vagrantfiles for single file Virtual Server installations, and instructions for isolating 
NSoT inside Mac OS X.  

1. Install NSoT into a clean Debian or Ubuntu Distro:
=====================================================
NSoT runs well inside both Debian and Ubuntu servers, and is considered front line stable.
Assuming you have just installed Debian or Ubuntu 12.* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-Ubuntu-Install`

2. Install NSoT into a clean CentOS Distro:
===========================================
NSoT runs well inside CentOS servers, and is considered front line stable.
Assuming you have just installed CentOS 12.* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-CentOS-Install`

3. Install NSoT into clean a Fedora Distro:
===========================================
NSoT runs well inside Fedora servers, and is considered front line stable.
Assuming you have just installed Fedora 22* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-Fedora-Install`

4. Install NSoT into clean SuSe Distro:
=======================================
NSoT runs well inside SuSe servers, and is considered front line stable.
Assuming you have just installed SuSe 13.* from source, you will need to run these commands to install NSoT.
Start with the Demo, and then configure as needed.

    :doc:`/NSoT-SuSe-Install`


5. NSoT in Python Virtual Environment on Mac (local)
====================================================
NSoT can be installed natively onto any Mac OS X that has python. However we reccomend putting the install into 
a virtual environment, isolating the install of python, and a few other tweaks to make sure your install runs smoothly.

    :doc:`nsot-mac-python`


6. Vagrant Virtual Servers inside Mac OSX
=========================================
NSoT is available via Vagrantfile for multiple linux distributions. A Vagrantfile builds a particular linux distro, installs the prerequisites, 
(python, pip, mrproxy)  and finally installs NSoT with a single command line entry.  Vagrant allows users to provision multiple virtual machines 
and is an excellent way to see our software in differing environments. The real advantage to vagrant virtual servers; simplicity.

  a. One command to build a linux disto with NSoT preconfigured.
  b. One command to log into the server.
  c. One command to start the NSoT service, build the database, and begin operation. 
  d. When you are done, one command to destroy the vagrant server, and all of it`s trimmings.

    :doc:`/nsot-vagrant`

CentOS 12 Vagrantfile
---------------------
    :doc:`/nsot-centos-vagrant` 
     - `Vagrantfile <https://github.com/dropbox/nsot/tree/master/vagrant-files/centos/Vagrantfile>`_

Debian 12 Vagrantfile
---------------------
    :doc:`/nsot-debian-vagrant`
     -  `Vagrantfile <https://github.com/dropbox/nsot/tree/master/vagrant-files/debian/Vagrantfile>`_

Fedora 22 Vagrantfile
---------------------
    :doc:`/nsot-fedora-vagrant`
     -  `Vagrantfile <https://github.com/dropbox/nsot/tree/master/vagrant-files/fedora/Vagrantfile>`_

SuSe 13 Vagrantfile
-------------------
    :doc:`/nsot-suse-vagrant`
     -  `Vagrantfile <https://github.com/dropbox/nsot/tree/master/vagrant-files/suse/Vagrantfile>`_

Ubuntu 12.4 Vagrantfile
-----------------------
    :doc:`/nsot-ubuntu-vagrant`
     -  `Vagrantfile <https://github.com/dropbox/nsot/tree/master/vagrant-files/ubuntu/Vagrantfile>`_




