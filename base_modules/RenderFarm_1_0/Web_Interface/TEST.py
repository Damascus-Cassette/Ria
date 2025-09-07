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

    # @IO_websocket('Path')
    # async def WS_Manager_to_Client(this_entity:Entity, other_entity:Entity, request : Request, websocket: WebSocket):
    #     #https://www.starlette.io/websockets/
    #     websocket.accept()
    #     try:
    #         while True:
    #             a = await websocket.recieve_message()
    #             intake_message(a)
    #             if criteria.get():
    #                 websocket.close()
    #     except:
    #         ...?
    
    Interface_Websocket = IO_websocket('Path')

    @Interface_Websocket.manager.on_request() #Accept or deny
    @Interface_Websocket.manager.on_open()    #After accepting
    @Interface_Websocket.manager.on_message() #On message recieve
    @Interface_Websocket.manager.on_error()   #On error in event loop
    @Interface_Websocket.manager.on_close()   #Gracefully closing the event

    @Interface_Websocket.manager.CustomManager()
    async def WS_Manager_to_Client(self, events, this_entity:Entity, other_entity:Entity, request : Request, websocket: WebSocket):
        ''' I could wrap the events, but this gives more control'''
        #https://www.starlette.io/websockets/
        websocket.accept()
        events.on_load()
        try:
            while True:
                a = await websocket.recieve_message()
                events.on_load()
                intake_message(a)
                if criteria.get():
                    events.on_load()
                    websocket.close()
        except:
            ...?

    #Have this as as default with connection objects and inherit the hooks added bellow?
    @Interface_Websocket.client.CustomClient() #Evaluates header & interface, and all that like normal
    async def WS_Client_to_Manager(self,this_entity, other_entity, path, header, preset_kwargs):
        ws = websocket.WebSocketApp(path,
                                header = header,
                                **preset_kwargs)
        ws.run_forever(dispatcher=rel, reconnect=5)
        other_entity.ws_pool.append(ws)
            #Meaning the foreign_entity holds the ws object.
        return ws
    
    @Interface_Websocket.client.on_open()
    @Interface_Websocket.client.on_message()
    @Interface_Websocket.client.on_error()
    @Interface_Websocket.client.on_close()
    def event(self, this_entity, other_entity, path, and_event_args_kwargs):
        ...