import urllib

from scoring_engine.engine.basic_check import BasicCheck


class HTTPPostCheck(BasicCheck):

    def command(self):
        args = self.command_format(self.properties)
        sanitized_args = []
        for arg in args:
            if type(arg) is str:
                sanitized_args.append(urllib.parse.quote(arg))
            else:
                sanitized_args.append(arg)
        cmd = self.CMD.format(*sanitized_args)
        return cmd
