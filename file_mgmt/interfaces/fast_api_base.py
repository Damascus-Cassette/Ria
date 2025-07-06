''' Base module for wrappers and common functions '''

def message[T](func:T)->T:
    ''' Initialize message class with args '''
    return _message(func)
    

class _message():
    callbacks = []
    
    def __init__(self,func):
        self.func = func

    def __call__(self,*args,**kwargs):
        return self.func(,*args,**kwargs)

    def handle_responce(self,message):
        if message.is_error:
            return self.error(message)
        else:
            return self.callback(message)


    def callback(self,func):
        def func():
            ...
        self.callback = func
        
        return func
        
    def error(self,func):
        ''' Create function that handles error reporting'''
        def func(self,):
            ...
        
        self.error = func
        return func