from types import CoroutineType, AsyncGeneratorType
from inspect import iscoroutinefunction, isasyncgenfunction, isasyncgen, iscoroutine
import asyncio 

class Scheduled_Task():
    def __init__(self,func,*args,**kwargs):
        self.func   = func
        self.args   = args
        self.kwargs = kwargs

    _timer : CoroutineType
    continue_execution: bool
    

    def run(self, interval):
        self.interval = interval
        asyncio.create_task(self._consumer(self._loop()))

    @staticmethod
    async def _consumer(generator:AsyncGeneratorType):
        ''' Consumes the generator '''
        async for x in generator: ...
        await generator.aclose()


    async def _loop(self):
        ''' Generator func, running func that's not a generator'''
        self.continue_execution = True
        self.is_running         = True
        try: 
            while self.continue_execution:
                yield
                await self._tick()
            await self._post()
        # except StopAsyncIteration:...
        # except StopIteration:...
        except:raise
        finally:
            await self._finalize()

        

    async def _tick(self,):
        self.func(self,*self.args,**self.kwargs)
        self.timer = asyncio.create_task(asyncio.sleep(self.interval))
        try:
            await self.timer
        except asyncio.CancelledError:
            return

    async def _post(self,):
        ...

    async def _finalize(self,):
        print('TASK WAS FINALIZED')
        self.timer      = None
        self.is_running = False

    def close(self, finalize:bool=None):
        self.continue_execution = False
        if finalize is not None:
            _fin = self.finalize
            self.finalize = finalize
            self.timer.cancel()
                #Should close timer, run rest of tick and complete the loop.
            self.finalize = _fin
        else:
            self.timer.cancel()
            # await self.timer.close()

async def main():
    a = Scheduled_Task(lambda task: print('Hello'))
    b = Scheduled_Task(lambda task: print('Hello1'))
    a.run(1)
    b.run(1)
    await asyncio.sleep(5)
    a.close()
    await asyncio.sleep(5)
    b.close()
    await asyncio.sleep(5)
    

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()