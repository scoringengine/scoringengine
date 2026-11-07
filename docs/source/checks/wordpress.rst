WordPress
^^^^^^^^^
Logs into WordPress by POSTing the account's credentials to the login page and following redirects. Use content only shown after a successful login (e.g. ``Welcome to WordPress!``) as the matching content.

`Uses Accounts`

Custom Properties:

.. list-table::
   :widths: 25 50

   * - useragent
     - specific useragent to use in the request
   * - vhost
     - vhost used in the request
   * - uri
     - login page path (Ex: /wp-login.php)
