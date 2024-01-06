#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE testdb;
    CREATE USER bender WITH PASSWORD '1234pass';
    CREATE USER dscott WITH PASSWORD 'password1';
    CREATE USER ttesterson WITH PASSWORD 'somepass';
EOSQL