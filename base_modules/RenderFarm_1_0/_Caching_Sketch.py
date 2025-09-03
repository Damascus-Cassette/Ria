class Cache():
    data : dict

    

class cache_item():
    key  : str      #Unique string
    data : dict     #typed dict


class cache_io():

    ''' Container per node of cache settings & interactions '''
    
    def asscociate_key(self,  key : str, asc_with_cached = False):
        ''' Flag input key to ascociate with sucessfeull result (with_cached means asc with cached) '''

    def search_key(self, key, future_asc = False, asc_with_cached = False)->cache_item|_unset:
        ''' Search for key in caches. Return none if not found. '''

    def asscociate(self, *values, asc_with_cached = False): #Asc with a colision of a pre-exisitng cache
        ''' Asscociate potential result with key derived from values, default to allowed to asc with pre-existing cache ''' 

    def search(self    , 
               *values ,            # Values that are parsed into key. ORDER MATTERS! 
               future_asc = False,  # Note key on node for when execution completes to asc resulting cache object with above hash. 
                                        # Good for when i0, i2, are deterministic to result, but i3 is required to complete result and is computationally heavy. (xor / data reconstruction like logic)
                                        # Or for custom keys.
               asc_with_cached = False,
               )->cache_item|_unset:
        ''' Searches relevent areas for this cached value, local or otherwise. Returns a cache. '''
        
    def search_contextually(self, future_asc = False, asc_with_cached = False)->cache_item|_unset:
        ''' Search the values passed through incoming sockets in execute automatically '''

    def search_memo()->cache_item|_unset:
        ...

from inspect import isgeneratorfunction
class node():
    
    #Shape is i*3 o*1

    struct_key : str
    state_key  : property|str

    cache_io   : cache_io
    
    key_ascociateion = contextVar

    @hook(event = 'execute', mode='wrap', see_args = False)
    def _execute_wrapper_(self,func)-> FunctionType:
        if isgeneratorfunction(func): return self._make_cached_generator_wrapper_(func)
        return self._make_cached_wrapper_(func)
        
                        
    def _make_cached_wrapper_(self,func):
        def regular_wrapper(self,*args,**kwargs):
            t = self.key_ascociateion.set([])

            #check memo with structural
            if cache := self.cache_io.search_memo(keys = (self.state_key,self.struct_key)):
                res =  cache.retrieve(self)
                #ascociate keys w/a
                return res

            res = func(self,*args,**kwargs)
            #create cache w/a & ascociate keys
            if self.Cachable: 
                cache = cache_item.create(self, self.state_key, self.struct_key, self.deps_keys)
                Cache.intake(cache)
                Cache.ascociate(cache, self.key_ascociations.get())

            self.key_ascociateion.reset(t)

            return res

        return regular_wrapper

    def _make_cached_generator_wrapper_(self,func):    
        def generator_wrapper(self,*args,**kwargs):
            t = self.key_ascociateion.set([])

            if cache := self.cache_io.search_memo():
                res =  cache.retrieve(self)
            generator = func(self,*args,**kwargs)
            

            #Step to next yield, check if cache, asc keys and return if so. Else go to next iteration.
            for res in generator:
                if res is _unset:
                    continue
                elif isinstance(res,cache_item):
                    #Asc keys
                    #Intake
                    ...
                else:
                    # asc keys
                    # note execution
                    ...
            
            self.key_ascociateion.reset(t)
            #return res
        return generator_wrapper


    @hook_trigger('execute')
    def execute(self):
        cache = self.cache_io 
            #Prob contextval or similar
        
        i0 = self.in_sockets[0].execute()
        i1 = self.in_sockets[1].execute()

        yield cache.search(i0,i1, future_asc=True) #Meaning will find it via this cache next time

        i2 = self.in_sockets[2].execute()
        
        yield cache.search_contextually()
            #As in context 

        val = (i0 * i1 * i2)
        self.out_sockets[0].value = val
        
        return val
        #Technically not needed, but can be usefull,

    #Above executed once will first create 
        #state_key   -> cache({0:o0})
        #uuid(i0,i1) -> cache({0:o0}) 