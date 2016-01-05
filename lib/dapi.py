from websocket import create_connection
import json

import websocket
import threading
from time import sleep
from electrum_dash.plugins import run_hook

dapi = None

def on_message(ws, message):
    global dapi

    dapi.on_message(message)

def on_close(ws):
    print "### closed ###"

class DAPIWebSocket(object):    
    def start(self):
        websocket.enableTrace(True)
        self._ws = websocket.WebSocketApp("ws://localhost:5000/", on_message = on_message, on_close = on_close)
        self._wst = threading.Thread(target=self._ws.run_forever)
        self._wst.daemon = True
        self._wst.start()
        self._messages = []
        self._main_window = None

    def set_main_window(self, window):
        self._main_window = window

    def on_message(self, message):
        print "on_message", message
        obj = json.loads(message)
        if(obj["object"] == "dapi_message"):
            dapi.process_message(obj)

        print "11"
        self._messages.append(message)
        print "12"

    def send(self, json):
        self._ws.send(json)

    def receive(self):
        if len(self._messages) > 0: return self._messages.pop()
        return False

    def close(self):
        self._ws.close()

    def process_message(self, message):
        # { 
        #     "object" : "dapi_command",
        #     "data" : {
        #         "command" = "send_message",
        #         "sub_command" = "(addr,cmd2,cmd3)",
        #         "my_uid" = UID,
        #         "target_uid" = UID, 
        #         "signature" = "",
        #         "payload" = ENCRYPTED
        #     }
        # }
       
        print message

        if(message["object"] != "dapi_message"):
            return False

        print "100"

        if(message["data"]["command"] != "send_message"):
            return False

        print "101"

        if(message["data"]["sub_command"] == "addr-request"):
            username = self._main_window.wallet.storage.get('username', None)
            username2 = message["data"]["payload"]

            #in the demo all users can send all other users messages (friends can only send messages)
            addr = self._main_window.wallet.get_unused_address(self._main_window.current_account) #TODO: We need to keep track of these
            dapi.send_private_message(username, username2, "addr", addr)

        print "102"

        if(message["data"]["sub_command"] == "addr"):
            username2 = message["data"]["from_uid"] 
            addr = message["data"]["payload"] 

            if username2 in self._main_window.contacts:
                _type, obj = self._main_window.contacts[username2]

                if addr not in obj["addresses"]:
                    obj["addresses"].append(addr)

                self._main_window.contacts[username2] = ('friend', obj)
                #self._main_window.update_contacts_tab()     
                run_hook('contacts_tab_update', self._main_window.contacts)       

        if(message["data"]["sub_command"] == "tx-desc"):
            username2 = message["data"]["from_uid"] 
            tx_desc = json.loads(message["data"]["payload"]) 

            print tx_desc

            if "tx" not in tx_desc or "desc" not in tx_desc:
                print "Invalid tx description", tx_desc
                return

            print username2

            if username2 in self._main_window.contacts:
                _type, obj = self._main_window.contacts[username2]

                if "txes" not in obj:
                    obj["txes"] = []

                if tx_desc['tx'] not in obj["txes"]:
                    obj["txes"].append(tx_desc)
                else:
                    print "failed to append"

                print "1"
                self._main_window.contacts[username2] = ('friend', obj)
                self._main_window.update_history_tab()
                #run_hook('history_tab_update')
                #run_hook('set_label', tx_desc["tx"], tx_desc["desc"], True)
                print "2"
                print "10"
                self._main_window.update_contacts_tab()            
            else:
                print "missing user", username2

        if(message["data"]["sub_command"] == "payment-request"):
            username2 = message["data"]["from_uid"] 
            tx_desc = json.loads(message["data"]["payload"]) 

            if self._main_window.payment_request(username2, tx_desc):
                pass #should auto pay

        return True
    
    def send_invitation(self, myusername, target_email):        
        ex = {   
            "object" : "dapi_command",
            "data" : {
                "command" : "send_invitaiton",
                "my_uid" : myusername,
                "target_email" : target_email
            }
        }

        # send a message to DAPI
        s = json.dumps(ex)
        self.send(s)

        # wait for the result
        count = 0
        result = False
        while True:
            result = self.receive()
            if result:
                if(result.find('"dapi_result"') > 0):
                    obj = json.loads(result)
                    return obj["data"]["data"]
            
            sleep(.1)
            count += 1

            if count > 30:
                print "dapi.send_invitaiton timeout"
                return None

        print "dapi.send_invitaiton error"
        return None

    def get_profile(self, myusername, target_username):        
        ex = {   
            "object" : "dapi_command",
            "data" : {
                "command" : "get_profile",
                "my_uid" : myusername,
                "target_uid" : target_username, 
                "slot" : 1
            }
        }

        # send a message to DAPI
        s = json.dumps(ex)
        self.send(s)

        # wait for the result
        count = 0
        result = False
        while True:
            result = self.receive()
            if result:
                if(result.find('"dapi_result"') > 0):
                    obj = json.loads(result)
                    return obj["data"]["data"]
            
            sleep(.1)
            count += 1

            if count > 30:
                print "dapi.get_profile timeout"
                return None

        print "dapi.get_profile error"
        return None

    def send_private_message(self, myusername, target_username, sub_command, payload):
        ex = {   
            "object" : "dapi_command",
            "data" : {
                "command" : "send_message",
                "sub_command" : sub_command,
                "my_uid" : myusername,
                "target_uid" : target_username,
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


dapi = DAPIWebSocket()

try:
    dapi.start()
except:
    raise
    #print "DAPI is not running"

