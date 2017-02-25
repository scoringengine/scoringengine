from scoring_engine.engine.basic_check import BasicCheck


class DNSCheck(BasicCheck):
    required_properties = ['qtype', 'domain']
    CMD = 'dig @{0} -t {1} -q {2}'

    def command_format(self, properties):
        return (self.get_ip_address(), properties['qtype'], properties['domain'])
