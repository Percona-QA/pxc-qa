import mysql.connector


class DbConnection:
    def __init__(self, user, socket):
        self.user = user
        self.socket = socket

    def connection_check(self):
        """ Method to test the cluster database connection.
            Since we are initializing the cluster using
            --initialize-insecure option we can login
            to database using default user (username : root)
            without password.
        """
        # Database connection string
        connection = mysql.connector.connect(host='localhost', user=self.user, unix_socket=self.socket)
        try:
            if connection.is_connected():
                # db_info = connection.get_server_info()
                return 0
        except Exception as e:
            print("Error while connecting to MySQL", e)
            return 1
        finally:
            # closing database connection.
            if connection.is_connected():
                connection.close()
