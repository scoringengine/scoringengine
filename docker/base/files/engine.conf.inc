[GENERAL]
checks_location = scoring_engine.engine.checks
check_timeout = 30
checks = ICMP,SSH,DNS,FTPDownload,FTPUpload,FTP,FTPS,HTTP,HTTPS,MYSQL,POSTGRESQL,POP3,POP3S,IMAP,IMAPS,SMTP,SMTPS,VNC
timezone = US/Eastern

[DB]
# SQLite
uri = mysql://se_user:CHANGEME@mysql/scoring_engine

[REDIS]
host = redis
port = 6379
password =
