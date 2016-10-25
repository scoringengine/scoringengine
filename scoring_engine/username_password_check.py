from basic_check import BasicCheck


class UsernamePasswordCheck(BasicCheck):

    def set_credentials(self, username, password):
        self.username = username
        self.password = password
