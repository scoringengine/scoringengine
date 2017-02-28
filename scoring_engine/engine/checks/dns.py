from scoring_engine.engine.basic_check import BasicCheck


class DNSCheck(BasicCheck):
    required_properties = ['qtype', 'domain']
    CMD = 'dig @{0} -p {1} -t {2} -q {3}'

    def command_format(self, properties):
        return (self.ip_address, self.port, properties['qtype'], properties['domain'])
