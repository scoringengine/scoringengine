from scoring_engine.engine.basic_check import BasicCheck


class UsernamePasswordCheck(BasicCheck):

    def set_credentials(self, username, password):
        self.username_value = username
        self.password_value = password

    @property
    def username(self):
        return self.username_value

    @property
    def password(self):
        return self.password_value
