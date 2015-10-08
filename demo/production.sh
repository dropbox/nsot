#!/bin/bash

# Turn Demo Server into a Light Production or Test Server
# This file allows users to repeatedly start the demo server without
# overwriting the data.
# Users can stand up a server, work on the data, and count on it being there
# the next time they log in.

# Start With the Settings
export NSOT_CONF=$(pwd)/demo_settings.py

# Start user proxy
# nsot is set to listen on all ports (0.0.0.0)
#  respond to un-authenticated traffic on port 8990
#  respond to authenticated traffic on port 8991
nsot-server user_proxy -a 0.0.0.0 -P 8990 -p 8991 admin &

# Start web service
# must be performed from the directory where nsot was installed, or
# re-installed globally
nsot-server start

# Kill the user_proxy once we exit (Linux only)
fuser -k 8991/tcp
