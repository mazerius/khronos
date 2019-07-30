# import datetime
# import websocket
# import requests
# import time
# import json
#
# def connectToWebSocket():
#     print(datetime.datetime.now(), "| [GatewayManager]: Connecting to websocket...")
#     websocket.enableTrace(True)
#     print(datetime.datetime.now(), "| [GatewayManager]: Attempting to create connection to websocket...")
#     try:
#         ws = websocket.create_connection("ws://" + "0.0.0.0" + ":" + str(4999) + '/events')
#         print(datetime.datetime.now(), "| [GatewayManager]: Successfully connected to websocket.")
#         while True:
#             print('waiting')
#             ws.send('hello')
#             time.sleep(5)
#     except ConnectionError as e:
#         print(e)
#         print(datetime.datetime.now(), "| [GatewayManager]: ConnectionError occured. Attempting to reconnect...")
# #ws = connectToWebSocket()
# requests.put('http://127.0.0.1:4999/broadcast', data=json.dumps({'hello':1}), headers= {'Content-Type': 'application/json'})
#
#
