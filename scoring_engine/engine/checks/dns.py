from scoring_engine.engine.basic_check import BasicCheck


class DNSCheck(BasicCheck):
    PROP_QTYPE = 'qtype'
    PROP_DOMAIN = 'domain'
    CMD = 'dig @{0} -t {1} -q {2}'

    def command(self):
        dig_args = self.get_property_tuple()
        cmd = self.CMD.format(*dig_args)
        return cmd

    def get_property_tuple(self):
        """
        Given a dns_environment, extract the qtype and domain property
        Returns a tuple of ip,qtype,domain for dig command
        """
        ip = self.get_ip_address()
        if len(self.environment.properties) != 2:
            raise LookupError('Not enough DNS Environment Properties to issue query')
        qtype = self.get_property_by_name(self.PROP_QTYPE)
        domain = self.get_property_by_name(self.PROP_DOMAIN)
        return (ip, qtype, domain)
