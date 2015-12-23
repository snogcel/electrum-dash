from websocket import create_connection
import json

class DAPIWebSocket(object):    
    def start(self):
        self._ws = create_connection("ws://localhost:5000")

    def send(self, json):
        self._ws.send(json)

    def receive(self):
        result =  self._ws.recv()
        if not result: return False
        return result

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
