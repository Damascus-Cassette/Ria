import websocket
import _thread
import time
import rel

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://api.gemini.com/v1/marketdata/BTCUSD",
                              on_open    = on_open,
                              on_message = on_message,
                              on_error   = on_error,
                              on_close   = on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

class Interface():

    @IO_websocket('Path')
    async def WS_Manager_to_Client(this_entity:Entity, other_entity:Entity, request : Request, websocket: WebSocket):
        #https://www.starlette.io/websockets/
        websocket.accept()
        try:
            while True:
                a = await websocket.recieve_message()
                intake_message(a)
                if criteria.get():
                    websocket.close()
        except:
            ...?
    
    #Have this as as default with connection objects and inherit the hooks added bellow?
    @WS_Manager_to_Client.CustomClient() #Evaluates header & interface, and all that like normal
    async def WS_Client_to_Manager(self,this_entity, other_entity, path, header, preset_kwargs):
        ws = websocket.WebSocketApp(path,
                                header = header,
                                **preset_kwargs)
        ws.run_forever(dispatcher=rel, reconnect=5)
        other_entity.ws_pool.append(ws)
            #Meaning the foreign_entity holds the ws object.
        return ws
    
    @WS_Manager_to_Client.client.on_open()
    @WS_Manager_to_Client.client.on_message()
    @WS_Manager_to_Client.client.on_error()
    @WS_Manager_to_Client.client.on_close()
    