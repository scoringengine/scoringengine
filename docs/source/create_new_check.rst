Create New Service Check
************************

Each service check (DNS, SSH, ICMP etc) are essentially simple commands that the worker will execute and gather the output of. This output is then handled by the engine to determine if a service check is successful or not for that round.

For the sake of explaination, we'll be walking through our documentation by taking a look at the SSH check.

Create Check Source File
------------------------

Each check is stored in the `scoring_engine/checks <https://github.com/scoringengine/scoringengine/blob/master/scoring_engine/checks>`_ directory.

Let's take a look at what the SSH check file looks like (scoring_engine/checks/ssh_check.py):


.. code-block:: python
   :linenos:
   :emphasize-lines: 3,5

   class SSHCheck(BasicCheck):
      required_properties = ['commands']
      CMD = CHECKS_BIN_PATH + '/ssh_check {0} {1} {2} {3} {4}'

      def command_format(self, properties):
          account = self.get_random_account()
          return (
              self.host,
              self.port,
              account.username,
              account.password,
              properties['commands']
          )

.. note:: The main point of each check source code, is to generate a command string. The format of this string is defined in the CMD variable. The plugin executes the command_format function, which outputs a list of the parameters to fill in the formatted CMD variable.


- **Line 1** - This is the Class name of the check, and will need to be something you reference in bin/competition.yaml
- **Line 2** - We specificy what properties this check requires. This can be any value, as long as it's defined in bin/competition.yaml.
- **Line 3** - This is the format of the command. The SSH Check requires an additional file to be created in addition to this file, which will be stored in CHECKS_BIN_PATH (this is scoring_engine/checks/bin). We're also specifying placeholders as parameters, as we will generate dynamically. If the binary that the command will be running is already on disk, (like ftp or nmap), then we don't need to use the CHECKS_BIN_PATH value, we can reference the absolute path specifically.
- **Line 5** - This is where we specify the custom parameters that will be passed to the CMD variable. We return a list of parameters that gets filled into the CMD.
- **Line 6** - This function provides the ability to randomly select an account to use for credentials. This allows the engine to randomize which credentials are used each round.

Now that we've created the source code file, let's look at what custom shell script we're referring to in the check source code.

::

  #!/usr/bin/env python

  # A scoring engine check that logs into SSH and runs a command
  # The check will login each time and run ONE command
  # The idea of running separate sessions is to verify
  # the state of the machine was changed via SSH
  # IE: Login, create a file, logout, login, verify file is still there, logout
  #
  # To install: pip install -I "cryptography>=2.4,<2.5" && pip install "paramiko>=2.4,<2.5"

  import sys
  import paramiko


  if len(sys.argv) != 6:
      print("Usage: " + sys.argv[0] + " host port username password commands")
      print("commands parameter supports multiple commands, use ';' as the delimeter")
      sys.exit(1)

  host = sys.argv[1]
  port = sys.argv[2]
  username = sys.argv[3]
  password = sys.argv[4]
  commands = sys.argv[5].split(';')

  # RUN SOME CODE
  last_command_output = "OUTPUT FROM LAST COMMAND"

  print("SUCCESS")
  print(last_command_output)


For the sake of copy/paste, I've removed what code is actually run for SSH, but that can be seen  `here <https://github.com/scoringengine/scoringengine/blob/master/scoring_engine/checks/bin/ssh_check>`_.


As we can see, this is just a simple script (and can in fact be any language as long as it's present on the worker), that takes in a few parameters, and prints something to the screen. The engine takes the output from each command, and determines if a check is successful by matching that against the matching_content value defined in bin/competition.yaml. Any output from this command will also get presented in the Web UI, so it can be used for troubleshooting purposes for white/blue teams.

In this example, our matching_content value will be "SUCCESS".

Create Service Definition
-------------------------

Now that we've created our check source code, we now need to add it to the competition so that it will run!

.. code-block:: yaml
   :linenos:
   :emphasize-lines: 3,5

   - name: SSH
     check_name: SSHCheck
     host: testbed_ssh
     port: 22
     points: 150
     accounts:
     - username: ttesterson
       password: testpass
     - username: rpeterson
       password: otherpass
     environments:
     - matching_content: "^SUCCESS"
       properties:
       - name: commands
         value: id;ls -l /home
     - matching_content: PID
       properties:
       - name: commands
         value: ps

- **Line 1** - The name of the service. This value must be unique per team and needs to be defined for each team.
- **Line 2** - This is the classname of the check source code. This is how we tell the engine which check plugin we should execute.
- **Line 3** - The host/ip of the service to check.
- **Line 4** - The port of the service to check.
- **Line 5** - The amount of points given per successful check per round.
- **Line 6-10** - A list of credentials for this service. Each round, the engine will randomly select a set of credentials to use.
- **Line 11-19** - A list of environments for this service. Each round, the engine will randomly select an environment to use. This allows for the flexibility of running one SSH command this round, but another command another round, and so on.
- **Line 12** - We match this value against the output from the check command, and compare it to identify if the check is Successful or not. We define it per environment, as this might change depending on the properties for each round.
- **Line 13-15** - The properties defined in the check source code. Notice how we said the 'commands' property was required in the check source? This is where we define all of those properties. The value is whatever value this property should be.


Contribute Check to Repository
------------------------------

Depending on the check and what it does, we might be interested in including your check into our github repository!

Create Unit Test File
^^^^^^^^^^^^^^^^^^^^^

Each check source code has a corresponding unit test, which simply generates a test CMD, and compares that against the expected command string.

An example unit test for SSH looks like this (tests/scoring_engine/checks/test_ssh.py):

.. code-block:: python
   :linenos:
   :emphasize-lines: 3,5

   from scoring_engine.engine.basic_check import CHECKS_BIN_PATH

   from tests.scoring_engine.checks.check_test import CheckTest


   class TestSSHCheck(CheckTest):
       check_name = 'SSHCheck'
       properties = {
           'commands': 'ls -l;id'
       }
       accounts = {
           'pwnbus': 'pwnbuspass'
       }
       cmd = CHECKS_BIN_PATH + "/ssh_check '127.0.0.1' 1234 'pwnbus' 'pwnbuspass' 'ls -l;id'"

- **Line 1** - Since we're adding additional files, we want to use the dynamically created CHECKS_BIN_PATH variable.
- **Line 3** - Import the CheckTest parent class which all check tests inherit from.
- **Line 6** - Create the unit test class. The classname must start with 'Test'.
- **Line 7** - This points to the classname of the check source code.
- **Line 8-10** - Define an example set of properties the test will use.
- **Line 11-13** - Define an example set of credentials the test will use.
- **Line 14** - Define an expected command string to verify the check source code works as expected.


Verify Unit Test
^^^^^^^^^^^^^^^^
::

  py.test tests/scoring_engine/checks/test_ssh.py

If all is well, then commit these files and `Create a PR <https://github.com/scoringengine/scoringengine/pulls>`_
