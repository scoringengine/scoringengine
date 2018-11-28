LDAP
^^^^
Uses ldapsearch to login to ldap server. Once authenticated, it performs a lookup of all users in the same domain

`Uses Accounts`

Custom Properties:

.. list-table::
   :widths: 25 50

   * - domain
     - domain of the username
   * - base_dn
     - base dn value of the domain (Ex: dc=example,dc=com)
