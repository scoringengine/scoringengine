from scoring_engine.engine.basic_check import BasicCheck


class TCPCheck(BasicCheck):
    """Verify a TCP port accepts connections (no protocol-level validation).

    Uses netcat in zero-I/O mode. On success netcat-openbsd prints
    "Connection to <host> <port> port [tcp/*] succeeded!", so set the
    environment's matching_content to "succeeded".
    """

    required_properties = ["timeout"]
    CMD = "timeout {0} nc -zv {1} {2}"

    def command_format(self, properties):
        return (int(properties["timeout"]), self.host, self.port)
