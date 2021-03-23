Web
---

Install MySQL Server
^^^^^^^^^^^^^^^^^^^^
::

  apt-get install -y mariadb-server
  sed -i -e 's/127.0.0.1/0.0.0.0/g' /etc/mysql/mysql.conf.d/mysqld.cnf
  systemctl restart mysql

Setup MySQL
^^^^^^^^^^^
::

  mysql -u root -p<insert password set during installation>
  CREATE DATABASE scoring_engine;
  CREATE USER 'engineuser'@'%' IDENTIFIED BY 'enginepass';
  GRANT ALL on scoring_engine.* to 'engineuser'@'%' IDENTIFIED by 'enginepass';

Install Nginx
^^^^^^^^^^^^^
::

  apt-get install -y nginx

Setup SSL in Nginx
^^^^^^^^^^^^^^^^^^
::

  mkdir /etc/nginx/ssl
  cd /etc/nginx/ssl
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt

Copy nginx config
^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/configs/nginx.conf /etc/nginx/sites-available/scoring_engine.conf
  ln -s /etc/nginx/sites-available/scoring_engine.conf /etc/nginx/sites-enabled/
  rm /etc/nginx/sites-enabled/default
  systemctl restart nginx

Setup web service
^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/configs/web.service /etc/systemd/system/scoring_engine-web.service

Modify configuration
^^^^^^^^^^^^^^^^^^^^
::

  vi /home/engine/scoring_engine/src/engine.conf

Install uwsgi
^^^^^^^^^^^^^
::

  pip install uwsgi

Start web
^^^^^^^^^
::

  systemctl enable scoring_engine-web
  systemctl start scoring_engine-web

Monitoring
^^^^^^^^^^
::

  journalctl -f _SYSTEMD_UNIT=scoring_engine-web.service
  tail -f /var/log/scoring_engine/web.log
  tail -f /var/log/scoring_engine/web-nginx.access.log
  tail -f /var/log/scoring_engine/web-nginx.error.log
