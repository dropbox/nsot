#!/bin/bash

export NSOT_CONF=$(pwd)/demo_settings.py
DB_FILE=$(pwd)/demo.sqlite3

# Only create the database if it doesn't exist.
if [ ! -f ${DB_FILE} ]; then
    # Create the database.
    echo "Database not found; creating database..."
    nsot-server upgrade --noinput

    # Load demo data fixtures.
    echo -e "\nLoading demo data fixtures..."
    nsot-server loaddata demo_fixtures
else
    echo -e "Database already exists; continuing..."
fi

# Start web service
echo "Starting web service..."
nsot-server start
