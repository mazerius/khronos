from websocket_server import WebsocketServer
import threading
import websocket
import datetime



# Responsible for creating a websocket and writing data to it.

class WebSocketThread(object):
    """ Threading websocket server class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, name, port, address):
        threading.Thread.__init__(self)
        thread = threading.Thread(target=self.run, args=())
        self.name = name
        self.port = port
        self.address = address
        thread.daemon = True # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        """ Method that runs forever """
        webSocketServerThread = WebSocketServerThread(self.name, self.port, self.address)
        webSocketServerThread.daemon = True
        webSocketServerThread.start()
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://" + self.address + ':' + self.port)
        while True:
            pass

    # sends a message down the websocket
    def publish(self, message):
        self.ws.send(message)

# responsible for creating and keeping the websocket alive
class WebSocketServerThread(threading.Thread):

    def __init__(self, name, port, address):
        threading.Thread.__init__(self)
        self.name = name
        self.port = port
        self.address = address

    def run(self):
        # broadcasts the received message to all websocket clients
        def broadcast(client, server, message):
            for client in server.clients:
                if client["server_port"] == server.port:
                    server.send_message(client, message)

        def new_client(client, server):
            client["server_port"] = server.port



        print(datetime.datetime.now(), "|Publisher |Thread | started", self.name, " @", self.address,
              self.port)
        self.server = WebsocketServer(int(self.port), host=self.address)
        self.server.set_fn_new_client(new_client)
        self.server.set_fn_message_received(broadcast)
        self.server.run_forever()
