Web
---

Install MySQL Server
++++++++++++++++++++
  apt-get install -y mysql-server
  sed -i -e 's/127.0.0.1/0.0.0.0/g' /etc/mysql/mysql.conf.d/mysqld.cnf
  systemctl restart mysql

Install Postgresql Server
+++++++++++++++++++++++++
  apt-get install -y postgresql postgresql-contrib postgresql-server-dev-9.5

Modify /etc/postgresql/9.5/main/postgresql.conf
  listen_addresses = '*'

Modify /etc/postgresql/9.5/main/pg_hba.conf
  host  all  all 0.0.0.0/0 md5
  systemctl restart postgresql

  su - postgres
  psql
  CREATE USER engineuser WITH PASSWORD 'enginepass';
  CREATE DATABASE scoring_engine;
  GRANT ALL PRIVILEGES ON DATABASE scoring_engine to engineuser;
  \q

Setup MySQL
+++++++++++
  mysql -u root -p<insert password set during installation>
  CREATE DATABASE scoring_engine;
  CREATE USER 'engineuser'@'%' IDENTIFIED BY 'enginepass';
  GRANT ALL on scoring_engine.* to 'engineuser'@'%' IDENTIFIED by 'enginepass';

Install Nginx
+++++++++++++
  apt-get install -y nginx

Setup SSL in Nginx
++++++++++++++++++
  mkdir /etc/nginx/ssl
  cd /etc/nginx/ssl
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt

Copy nginx config
+++++++++++++++++
  cp /home/engine/scoring_engine/src/configs/nginx.conf /etc/nginx/sites-available/scoring_engine.conf
  ln -s /etc/nginx/sites-available/scoring_engine.conf /etc/nginx/sites-enabled/
  rm /etc/nginx/sites-enabled/default
  systemctl restart nginx

Setup web service
+++++++++++++++++
  cp /home/engine/scoring_engine/src/configs/web.service /etc/systemd/system/scoring_engine-web.service

Modify configuration
++++++++++++++++++++
  vi /home/engine/scoring_engine/src/engine.conf

Enable production mode in configuration
+++++++++++++++++++++++++++++++++++++++
  sed -i -e 's/DEBUG = False/DEBUG = True/g' /home/engine/scoring_engine/src/scoring_engine/web/settings.cfg

Start web
+++++++++
  systemctl enable scoring_engine-web
  systemctl start scoring_engine-web

Monitoring
++++++++++
  journalctl -f _SYSTEMD_UNIT=scoring_engine-web.service
  tail -f /var/log/scoring_engine/web.log
  tail -f /var/log/scoring_engine/web-nginx.access.log
  tail -f /var/log/scoring_engine/web-nginx.error.log
