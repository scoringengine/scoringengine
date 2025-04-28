from scoring_engine.engine.basic_check import BasicCheck


class LDAPCheck(BasicCheck):
    required_properties = ['domain_base']
    CMD = "ldapsearch -x -H ldap://{0}:{1} -D cn={2},cn=Users,{3} -w {4} -b {3} '(objectclass=Domain)' cn"

    def command_format(self, properties):
        account = self.get_random_account()
        return (
            self.host,
            self.port,
            account.username,
            properties['domain_base'],
            account.password
        )
