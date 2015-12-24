from websocket import create_connection
import json

import websocket
import threading
from time import sleep

messages = []

def on_message(ws, message):
    print "on_message", message
    messages.append(message)

def on_close(ws):
    print "### closed ###"

class DAPIWebSocket(object):    
    def start(self):
        websocket.enableTrace(True)
        self._ws = websocket.WebSocketApp("ws://localhost:5000/", on_message = on_message, on_close = on_close)
        self._wst = threading.Thread(target=self._ws.run_forever)
        self._wst.daemon = True
        self._wst.start()

    def send(self, json):
        self._ws.send(json)

    def receive(self):
        if len(messages) > 0: return messages.pop()
        return False

    def close(self):
        self._ws.close()

    def get_profile(self, myusername, target_username):
        ex = {   
            "object" : "dapi_command",
            "data" : {
                "command" : "get_private_data",
                "my_uid" : myusername,
                "target_uid" : target_username, 
                "signature" : "SIG",
                "slot" : 1
            }
        }

        s = json.dumps(ex)
        print s
        self.send(s)

        count = 0
        result = False
        while True:
            result = self.receive()
            if result:
                print result
                if(result.find('"dapi_result"') > 0):
                    return result
            
            sleep(.1)
            count += 1

            if count > 30:
                print "dapi.get_profile timeout"
                return None

        print "dapi.get_profile error"
        return None

    def send_private_message(self, myusername, target_username, subcommand, payload):
        ex = {   
            "object" : "dapi_command",
            "data" : {
                "command" : "send_message",
                "subcommand" : subcommand,
                "my_uid" : myusername,
                "target_uid" : target_username,
                "signature" : "SIG",
                "payload" : payload
            }
        }

        s = json.dumps(ex)
        print "Send:", s
        self.send(s)

        count = 0
        result = False
        while True:
            result = self.receive()
            if result:
                print "Recieve:", result
                if(result.find('"dapi_message"') > 0):
                    return result
                    
            sleep(.1)
            count += 1

            if count > 30:
                print "dapi.get_profile timeout"
                return None

        print "dapi.get_profile error"
        return None
