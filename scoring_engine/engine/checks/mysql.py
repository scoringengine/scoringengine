from scoring_engine.engine.basic_check import BasicCheck

class MySQLCheck(BasicCheck):
    name = "MySQL Check"
    protocol = 'mysql'
    version = 'ipv4'

    def command(self):
        return 'mysql -h %s -u %s -p %s %s -e %s ' + %(self.get_ip_address())
