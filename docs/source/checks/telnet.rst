TELNET
^^^^^^
Logs into a system using Telnet with an account/password, and executes command(s)

.. note:: Each command will be executed independently of each other in a separate telnet connection.

`Uses Accounts`

Custom Properties:

.. list-table::
   :widths: 25 50

   * - commands
     - ';' delimited list of commands to run (Ex: id;ps)
