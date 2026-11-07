import urllib

from scoring_engine.engine.basic_check import BasicCheck


class HTTPPostCheck(BasicCheck):
    """Checks whose CMD embeds args in a single-quoted form body: URL-encode them."""

    def quote_arg(self, arg):
        return urllib.parse.quote(arg)
