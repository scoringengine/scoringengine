from scoring_engine.engine.basic_check import BasicCheck


class LDAPCheck(BasicCheck):
    required_properties = ['domain', 'base_dn']
    CMD = "ldapsearch -x -h {0} -p {1} -D {2}@{3} -b {4} -w {5} '(objectclass=User)' cn"

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            properties['domain'],
            properties['base_dn'],
            account.password
        )
