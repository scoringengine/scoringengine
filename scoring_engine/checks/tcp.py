from scoring_engine.engine.basic_check import BasicCheck


'''
Success - Connection to 192.168.0.100 22 port [tcp/ssh] succeeded!
Failure - nc: connect to 192.168.0.99 port 22 (tcp) timed out: Operation now in progress
'''
class TCPCheck(BasicCheck):
    required_properties = []
    CMD = "nc -zv -w 3 {0} {1}"

    def command_format(self, properties):
        return (
            self.host,
            self.port,
        )
