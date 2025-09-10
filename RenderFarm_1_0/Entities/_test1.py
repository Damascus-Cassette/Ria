from types import GeneratorType, FunctionType, CoroutineType, AsyncGeneratorType
import asyncio
from inspect import isasyncgenfunction, isasyncgen, iscoroutinefunction, isgeneratorfunction


class Scheduled_Task():
    generator        : GeneratorType|AsyncGeneratorType

    current_timer    : CoroutineType
    current_loop     : CoroutineType

    is_running       : bool = False
    continue_running : bool = False
    finalize         : bool = True

    func : FunctionType = None

    def __init__(self, func, *args, **kwargs):
        self.func      = func
        self.args      = args
        self.kwargs    = kwargs

    async def start(self, interval, start_delay=None, last_ran=None):
        assert self.is_running is False
        self.continue_running = True
        if start_delay:
            await asyncio.sleep(start_delay)
        self.interval = interval
        # if last_ran:
        #     dif = max(current_time-last_ran, 0)
        #     if dif: asyncio.sleep(dif)
        if isasyncgenfunction(self.func) or isgeneratorfunction(self.func):
            self.generator    = self.func(self, *self.args, **self.kwargs)
            self.current_loop = self._loop_generator(self.generator)
        else:
            self.current_loop = self._loop()
        
        async for item in self.current_loop:
            print('loop_iteration')

    def close(self, finalize = True ):
        self.continue_running = False
        _fin = self.finalize
        self.finalize = finalize 
        self.current_timer.close()
        # asyncio.gather(self.current_loop)
        self.finalize = _fin
    
    async def _loop(self):
        
        try:
            while self.continue_running:
                print('TICK!')
                await self._tick()
                yield
            await self._on_finalize()
        except StopIteration:
            ...
        except StopAsyncIteration:
            ...
        except Exception as e:
            raise e
        finally:
            await self._on_close()

    async def _tick(self):
        if iscoroutinefunction(self.func):
            await self.func(self,*self.args,**self.kwargs)
        else:
            self.func(self,*self.args,**self.kwargs)
        self.current_timer = asyncio.sleep(self.interval)
        await self.current_timer

    async def _on_finalize(self):
        if not self.finalize: return

    async def _on_close(self):
        self.is_running = False

    async def _loop_generator(self, generator):
        try:
            while self.continue_running:
                await self._tick_generator(generator)
                yield
            await self._on_finalize_generator(generator)
            
        except StopIteration:
            ...
        except StopAsyncIteration:
            ...
        except Exception as e:
            raise e
        finally:
            await self._on_close_generator()
    
    async def _tick_generator(self,generator):
        if isasyncgen(self.generator):
            anext(generator)
        else:
            next(generator)
        self.current_timer = asyncio.sleep(self.interval)
        await self.current_timer

    async def _on_finalize_generator(self,generator):
        ''' Only run if not cancled or finallized from inside the func '''
        if not self.finalize: return
        if isasyncgen(generator):
            anext(generator)
        else:
            next(generator)

    async def _on_close_generator(self):
        self.generator = None
        self.is_running = False


def function(schedule:Scheduled_Task, message:str):
    print('Starting Function!')
    i = 0
    while schedule.continue_running and (i < 3):
        print(message, f'iteration: {i}')
        i = i + 1    
        yield
    print('Finishing Function!')


scheduled_a = Scheduled_Task(function, message = 'ScheduledA')
scheduled_b = Scheduled_Task(function, message = 'ScheduledB')

async def main():
    a =  scheduled_a.start(1)
    b =  scheduled_b.start(2)
    asyncio.gather(a,b)

# scheduled_b.start(2)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()