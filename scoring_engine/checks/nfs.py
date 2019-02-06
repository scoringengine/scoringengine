from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class NFSCheck(BasicCheck):
    required_properties = ['remotefilepath', 'filecontents']
    CMD = CHECKS_BIN_PATH + '/nfs_check {0} {1} {2}'

    def command_format(self, properties):
        return (
            self.host,
            properties['remotefilepath'],
            properties['filecontents']
        )
