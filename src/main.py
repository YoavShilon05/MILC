import sys
from AssiClient import Client
import Connection
import Tray
from Settings import *

if __name__ == "__main__":

    connection = Connection.Connection()


    if len(sys.argv) < 2:
        raise SyntaxError("Beware! The file you have just ran relies and must be run with an argument parameter. "
                          "running it without one will surely cause it to fail critically. Please take the necessary "
                          "steps to make sure such accidents will not take place next time.")

    match (sys.argv[1]):
        case "init":
            connection.install()
        case "send":
            connection.send(sys.argv[2].replace("\\\\", "/").replace("\\", "/"))
        case "startup":
            connection.receive(True)
        case "recv":
            connection.receive()
        case "tray":
            tray = Tray.Tray(connection)
            tray.run_tray()
        case "sendto":
            with (Client(username, connection, True)) as client:
                client.send_file(sys.argv[2], sys.argv[3])
        case "update-users":
            connection.update_users()

        case _:
            raise ValueError("Beware! The Value entered for the above argument while running this very program has resulted "
                            "in a fatal error! please take the necessary steps to make sure this type of argument won't be "
                            "passed to this program any more.")
