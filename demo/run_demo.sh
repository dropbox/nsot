#!/bin/bash

export NSOT_CONF=./demo_settings.py

# Create the database.
echo "Creating database..."
nsot-server upgrade --noinput

# Load fixtures
echo -e "\nLoading fixtures..."
nsot-server loaddata demo_fixtures

# Start user proxy
nsot-server user_proxy -a 0.0.00 -P 8990 -p 8991 admin &

# Start web service
nsot-server start

# Kill the user_proxy once we exit (Linux only)
fuser -k 8991/tcp
