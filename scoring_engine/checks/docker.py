from scoring_engine.engine.basic_check import BasicCheck, CHECKS_BIN_PATH


class DockerAPICheck(BasicCheck):
    required_properties = ['docker_image']
    CMD = CHECKS_BIN_PATH + '/docker_check {0} {1} {2}'

    def command_format(self, properties):
        return (
            self.host,
            self.port,
            properties['docker_image']
        )
