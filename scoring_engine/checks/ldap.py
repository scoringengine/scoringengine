from scoring_engine.engine.basic_check import BasicCheck


class LDAPCheck(BasicCheck):
    required_properties = ['domain', 'base_dn']
    CMD = "ldapsearch -x -H 'ldap://{0}:{1}' -D 'cn={2},cn=Users,{3}' -w '{4}' -b '{3}' '(objectclass=User)' cn"

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            properties['domain_base'],
            account.password
        )
