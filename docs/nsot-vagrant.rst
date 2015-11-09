=================================
Vagrant on Mac w Virtualbox
=================================

NSoT engineers have built Vagrantfiles for you to deploy NSoT software in a multitude of linux environments. This tutorial will help you load a Macintosh computer (OS X) with Vagrant, Virtual Box, and dependencies so that you can start virtual servers and test the software.

NSoT publishes complete installation instructions for linux distributions, branch versions, and Vagrantfiles in addition to, not an alternative for the pip install method::

    $ pip-install nsot

The Goal:
=========
Install Brew, VirtualBox, Vagrant and  Vagrant-Manager, on a Macintosh 10.10.x system to deploy test versions of NSOT. When done we will be able to load a variety of linux distributions with NSOT pre-configured, as virtual servers inside a test environment.

Context:
========
We will use Vagrant and associated Virtual Server software to build NSoT on a variety of Linux distributions elsewhere in these documents. This guide is to help those unfamiliar with how to install and use Vagrant and Virtualbox, making the Vagrantfiles published more useful.

Vagrant allows us to provision complete virtual machines (Unix, Linux, Mac, or Windows) inside the Mac Operating system as virtual machines. The vagrant virtual servers are configured with a single file (called a “Vagrantfile.”) started with a single command (vagrant up), are contained within a single folder, and can be destroyed with a single command (vagrant destroy). This environment is nicely segregated from your day to day computing, and allows you to test our software in a variety of environments.

Assumptions:
============
You are running a computer with Mac OS X 10.10.x installed.
 
Overview:
=========

    1. Install Prerequisite Software (XCode).
    2. Install Homebrew, casks, and update.
    3. Brew Vagrant.
    4. Start your first server with Vagrant.


1. Install Prerequisite Software - XCode & XCode Tools:
=======================================================
Click link to Get Xcode —>             
https://itunes.apple.com/au/app/xcode/id497799835?mt=12

Agree to EULA and Install.

Install Prerequisite Software (XCode Tools from Command Line):
Open a Terminal (Launchpad —> Other —> Terminal).
At the command prompt run the following command to install XCode Tools::

    $ xcode-select —install 

- Accept the EULA.
- Agree to install at Prompt.

2. Install Prerequisite Software (Homebrew from Command Line):
==============================================================

Using the terminal, download and install Homebrew with this command::

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    
    
Run this command from the terminal to update and confirm install of Homebrew::

    $ brew doctor 


From Command line run these commands to update Brew and view the version (licenses)::

    $ brew update
    $ sudo xcodebuild -license 

3. Install Vagrant and Virtualbox via Homebrew:
===============================================

Download, verify, and install VirtualBox::

    $ brew install Caskroom/cask/virtualbox
    
Download, verify, and install VirtualBox extension pack for your version of virtualbox::

    $ brew install Caskroom/cask/virtualbox-extension-pack

Download, verify, and install Vagrant::

    $ brew install Caskroom/cask/vagrant

Download, verify, and install Vagrant-Manager::

    $ brew install Caskroom/cask/vagrant-manager
    
4. Start a Virtual Ubuntu Server:
=================================
Now that we have it all installed, let's spin up an Ubuntu server, log in to it, play, log out, and then destroy it.

From Command line enter the following to make a sandbox directory, cd into it, and then download the Ubuntu::

    $ mkdir sandbox && cd sandbox 
    $ vagrant box add precise64 http://files.vagrantup.com/precise64.box
    
Initialize the installation inside the sandbox folder (aka make the Vagrantfile). (You can modify the Vagrantfile and look at it after this step.)::

    $ vagrant init precise64 
    
Start the Ubuntu server via Vagrant by typing this at command line::

    $ vagrant up
    
To login to the new server via ssh, enter the following via command line::

    $ vagrant ssh
    
Change what you like. Mess it up if you care to. Once done poking around logout::

    $ exit
    
To destroy the Ubuntu virtual server installation::

    $ vagrant destroy
    
To rebuild from the OS again::

    $ vagrant up
    
Conclusion: After the login regimen finishes, you should be inside the new server you just created, for the second time. You have built a new server, Destroyed it, and built another in less time than it takes to drink a cup of coffee.


Footnotes:
Homebrew installation based on the guide published here.
http://coolestguidesontheplanet.com/installing-homebrew-os-x-yosemite-10-10-package-manager-unix-apps/

Based on the Vagrant installation guide published here.     
http://sourabhbajaj.com/mac-setup/Vagrant/README.html
