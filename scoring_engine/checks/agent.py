from scoring_engine.engine.basic_check import CHECKS_BIN_PATH, BasicCheck


class AgentCheck(BasicCheck):
    required_properties = []
    CMD = CHECKS_BIN_PATH + "/agent_check {0}"

    def command_format(self, properties):
        return (self.host, "")
