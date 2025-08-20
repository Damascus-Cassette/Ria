class enter_exit_hidden():
    def __init__(self,factory):
        self.factory = factory
    def __enter__(self):
        first_value =  next(self.factory)
        print('FIRST VALUE:', first_value)
        return first_value
    def __exit__(self,*args,**kwargs):
        # StopIteration
        try:
            next(self.factory)
        except StopIteration :
            pass
        except: 
            raise
        return None

# from inspect import isgeneratorfunction

# class potential_context():
#     def __init__(self,func):
#         assert isgeneratorfunction(func)
#         self.func = func

#     def make_context(self,*args,**kwargs):    
#         return enter_exit_hidden(self.func(*args,**kwargs))

#     def __call__(self,*args,**kwargs):
#         return self.func(*args,**kwargs )
#         ...
    

# @potential_context
# def func1():
#     ..

class custom_contextmanager():
    def __init__(self,func):
        self.func = func
    
    def __call__(self,*args,**kwargs):
        return self.func(*args,**kwargs) #Executing function once
        # return enter_exit_hidden(self.func(*args,**kwargs)) #Executing function once
    def contextual_generator(self,*args,**kwargs):
        return enter_exit_hidden(self.func(*args,**kwargs)) #Executing function once
    
    # def generator(self,**args,**kwargs):
    #     return enter_exit_hidden(self.func(*args,**kwargs)) #Executing function once
    
    # def __get__(self,instance,owner):
    #     #Python does not default to get when __enter__ and __exit__ are missing within the 'with' call
    #     return enter_exit_hidden(self.default())

    # def __enter__(self):
    #     return enter_exit_hidden(self.default)
        
    # def __exit__(self,*args,**kwargs):
    #     #WHen called, it's obscuring the erorr being raised
    #     ...

    # @staticmethod
    # def default():
    #     raise Exception('custom context manager must be initialized!')

@custom_contextmanager
def func1():
    #Generators can be thought to have a first 'invisible' yield that waits for the next() call to go to the first visible yeild
    print('a')
    yield 1
    print('b')
    # yield 'v'

with func1.contextual_generator() as a:
    # with func1():
        # print('c')
    print('c')
    print(a)

print(func1())
