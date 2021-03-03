#!/bin/bash

# Make sure we allow connections from external hosts
sudo sh -c 'echo "host all all samenet password" >> /etc/postgresql/10/main/pg_hba.conf'

sudo service postgresql start || exit 1

# Create some sample users for the engine to login with
USER_CREDENTIALS=( "bender:1234pass"
        "dscott:password1"
        "ttesterson:somepass" )
for creds in "${USER_CREDENTIALS[@]}" ; do
    USERNAME="${creds%%:*}"
    PASSWORD="${creds##*:}"
    sudo -u postgres sh -c "psql -c 'CREATE ROLE $USERNAME;'" || exit 1
    sudo -u postgres sh -c "psql -c \"ALTER ROLE $USERNAME WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN PASSWORD '$PASSWORD';\"" || exit 1
done

# Add the schema
sudo -u postgres sh -c "psql -c 'CREATE DATABASE testdb';" || exit 1

sudo service postgresql stop || exit 1
