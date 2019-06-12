import threading
from websocket_server import WebsocketServer
import datetime

# responsible for creating and keeping the websocket alive
class WebSocketServerThread(threading.Thread):

    def __init__(self, name, port, address):
        threading.Thread.__init__(self)
        thread = threading.Thread(target=self.run, args=())
        self.name = name
        self.port = port
        self.address = address
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        # broadcasts the received message to all websocket clients
        def broadcast(client, server, message):
            server.send_message_to_all(message)

        print(datetime.datetime.now(), "|Publisher |WebSocketServerThread | started", self.name, " @", self.address,
              self.port)
        self.server = WebsocketServer(int(self.port), host=self.address)
        self.server.set_fn_message_received(broadcast)
        self.server.run_forever()