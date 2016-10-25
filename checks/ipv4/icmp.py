from basic_check import BasicCheck


class ICMPCheck(BasicCheck):
    name = "ICMP IPv4 Check"
    protocol = 'ssh'
    version = 'ipv4'

    def command(self):
        return 'ping -c 1 ' + self.host_address
