from scoring_engine.engine.basic_check import BasicCheck


class ICMPCheck(BasicCheck):
    required_properties = []
    CMD = "ping -c 1 {0}"

    def command_format(self, properties):
        return (self.host, '')
