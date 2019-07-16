from flask import Flask
from flask_sockets import Sockets


app = Flask(__name__)
sockets = Sockets(app)

ws_list = []

@sockets.route('/events')
def echo_socket(ws):
    ws_list.append(ws)
    while not ws.closed:
        message = ws.receive()
        print('message received')
        print(ws_list)


@app.route('/')
def hello():
    print('received in /')
    for ws in ws_list:
        if not ws.closed:
            ws.send('helllllllllllo')
        else:
            # Remove ws if connection closed.
            ws_list.remove(ws)
    return 'ok'


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('0.0.0.0', 5001), app, handler_class=WebSocketHandler)
    server.serve_forever()