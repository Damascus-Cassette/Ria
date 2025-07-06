'''
This module is for interfaceing with the fast_api_manager.main instance through an external actor,
The primary assumption is that this client is wrapped in a seperate interface that handles the messages and security.

Each send command returns a callback function for responce, and each oncoming command corrisponds to a function to run.

For a basic implimentation without security see fast_api_client

This module manages on disk file creation and verification
'''

from .fast_api_dataclasses import standin


class main():

    def __init__(self, settings):
        ...

    @message
    def do_something(self)->standin:
        ...

    @do_something.callback('responce')
    def do_something_callback_responce():
        ...

    @do_something.callback('error')
    def do_something_callback_error():
        ...
    
    @order
    def order_from_server():
        ...
