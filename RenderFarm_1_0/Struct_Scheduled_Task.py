from types import CoroutineType, AsyncGeneratorType,GeneratorType
from inspect import iscoroutinefunction, isasyncgenfunction, isasyncgen, iscoroutine, isgeneratorfunction
import asyncio 

class Scheduled_Task():
    def __init__(self,func,*args,**kwargs):
        self.func   = func
        self.args   = args
        self.kwargs = kwargs

    _timer : CoroutineType
    continue_execution: bool
    
    def task(self, interval):
        self.interval = interval
        if not (isasyncgenfunction(self.func) or isgeneratorfunction(self.func)):
            return self._consumer(self._loop())
        else:
            generator = self.func(self,*self.args,**self.kwargs)
            return self._consumer(self._loop_through_generator(generator))
            
    @staticmethod
    async def _consumer(generator:AsyncGeneratorType):
        ''' Consumes the generator '''
        async for x in generator: ...
        await generator.aclose()


    async def _loop_through_generator(self, generator:AsyncGeneratorType|GeneratorType):
        ''' Generator func, running func that's not a generator'''
        self.continue_execution = True
        self.is_running         = True
        try: 
            while self.continue_execution:
                await self._tick_generator(generator)
                yield
            await self._post_generator(generator)
        except StopAsyncIteration:...
        except StopIteration:...
        except:raise
        finally:
            await self._finalize()

    async def _tick_generator(self,generator: AsyncGeneratorType|GeneratorType):
        if isasyncgen(generator): await anext(generator)
        else:                           next(generator)

        self.timer = asyncio.create_task(asyncio.sleep(self.interval))
        try:
            await self.timer
        except asyncio.CancelledError:
            return

    async def _post_generator(self,generator: AsyncGeneratorType|GeneratorType):
        if isasyncgen(generator): await generator.aclose()
        else:                           generator.close()
        

    async def _loop(self):
        ''' Generator func, running func that's not a generator'''
        self.continue_execution = True
        self.is_running         = True
        try: 
            while self.continue_execution:
                await self._tick()
                yield
            await self._post()
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
        self.timer      = None
        self.is_running = False

    def close(self, finalize:bool=None):
        self.continue_execution = False
        if self.timer is None: return
        if finalize is not None:
            _fin = self.finalize
            self.finalize = finalize
            self.timer.cancel()
            self.finalize = _fin
        else:
            self.timer.cancel()
    
    async def aclose(self, finalize:bool = False):
        self.close(finalize=finalize)


if __name__ == '__main__':
    async def _scheduled_generator(task):
        i = 0
        print('GENERATOR STARTING')
        try:
            while task.continue_execution:
                i = i + 1
                print(i)
                yield
        except GeneratorExit: #If not defined, rest of function will not run.
            print('GENERATOR EXIT CALLED')

        print('FINALIZING')

    async def _scheduled_generator_exit_early(task):
        i = 0
        print('GENERATOR STARTING')
        try:
            while task.continue_execution and i<7:
                i = i + 1
                print(i)
                yield
        except GeneratorExit:  #If not defined, rest of function will not run.
            print('GENERATOR EXIT CALLED')
        print('FINALIZING')

    async def main():
        a = Scheduled_Task(lambda task: print('Hello'))
        b = Scheduled_Task(_scheduled_generator)
        c = Scheduled_Task(_scheduled_generator_exit_early)
        asyncio.create_task(a.task(1))
        asyncio.create_task(b.task(1))
        asyncio.create_task(c.task(1))
        await asyncio.sleep(5)
        a.close()
        await asyncio.sleep(5)
        b.close()
        await asyncio.sleep(5)
        c.close()
        await asyncio.sleep(5)
        

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()