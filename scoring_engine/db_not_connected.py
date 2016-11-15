class DBNotConnected(Exception):
    def __str__(self):
        return "DB is not connected. Must connect first"
