from scoring_engine.engine.basic_check import BasicCheck


class ICMPCheck(BasicCheck):

    def command(self):
        return 'ping -c 1 ' + self.get_ip_address()
