#!/bin/sh
# db pack: MySQL, PostgreSQL and Microsoft SQL Server clients.
set -eu
curl -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb
dpkg -i /tmp/packages-microsoft-prod.deb
rm /tmp/packages-microsoft-prod.deb
apt-get update
ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
  default-mysql-client postgresql-client mssql-tools18 sqlcmd unixodbc-dev
