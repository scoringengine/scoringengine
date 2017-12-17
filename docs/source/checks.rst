Implemented Checks
*********************

DNS
^^^
Queries a DNS server for a specific record

Custom Properties:
  - qtype: the type of record (A, AAAA, CNAME, etc)
  - domain: the domain/host to query for

FTP(S)
^^^^^^
Uses the medusa command to login to an FTP server

Custom Properties:
  - none

FTPDownload
^^^^^^^^^^^
Logs in and downloads a specific file from the server's filesystem

Custom Properties:
  - filename: The relative path to download

FTPUpload
^^^^^^^^^^^
Logs in and uploads a specific file from the local filesystem to remote

Custom Properties:
  - filename: The relative path to upload

HTTP(S)
^^^^^^^
Sends a GET request to an HTTP(S) server

Custom Properties:
  - useragent: A specific useragent to use in the request
  - vhost: The vhost used in the request
  - uri: The uri of the request

ICMP
^^^^
Sends an ICMP Echo Request to server

Custom Properties:
  - none

IMAP(S)
^^^^^^^
Uses medusa to login to an imap server

Custom Properties:
  - domain: The domain of the username

MySQL
^^^^^
Logs into a MySQL server, uses a database, and executes a specific SQL command

Custom Properties:
  - database: The check will 'use database' before running command
  - command: The SQL command that will execute

POP3(S)
^^^^^^^
Uses medusa to login to an pop3 server

Custom Properties:
  - domain: The domain of the username

PostgreSQL
^^^^^^^^^^
Logs into a postgresql server, selects a database, and executes a SQL command

Custom Properties:
  - database: The postgres database to use
  - command: The SQL command that will get run

SMTP(S)
^^^^^^^
Logs into an SMTP server and sends an email

Custom Properties:
  - fromuser: The address that the email will be sent from
  - touser: The address that the email will be sent to
  - subject: The subject of the email
  - body: The body of the email

SSH
^^^
Logs into a system using SSH with an account/password, and executes command

Custom Properties:
  - command: The command that will run on the host after successful login

VNC
^^^
Connects and if specified, will login to a VNC server

Custom Properties:
  - none
