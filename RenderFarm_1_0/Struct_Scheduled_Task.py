from types import CoroutineType, AsyncGeneratorType,GeneratorType
from inspect import iscoroutinefunction, isasyncgenfunction, isasyncgen, iscoroutine, isgeneratorfunction
import asyncio 

class MaxIteratonsError(Exception):...

class Scheduled_Task():
    def __init__(self,func,*args,**kwargs):
        self.func   = func
        self.args   = args
        self.kwargs = kwargs

    _timer : CoroutineType
    continue_execution: bool
    
    def task(self, interval,start_delay=None,max_iterations=None):
        self.interval = interval
        self.max_iterations = max_iterations
        if not (isasyncgenfunction(self.func) or isgeneratorfunction(self.func)):
            return self._consumer(self._loop(),start_delay=start_delay,max_iterations=max_iterations)
        else:
            generator = self.func(self,*self.args,**self.kwargs)
            return self._consumer(self._loop_through_generator(generator),start_delay=start_delay,max_iterations=max_iterations)
            
    async def _consumer(self,generator:AsyncGeneratorType, start_delay = None, max_iterations=None):
        ''' Consumes the generator '''
        
        if start_delay:
            self._timer = asyncio.create_task(asyncio.sleep())
        try:
            await self._timer
        except asyncio.CancelledError:
            print('EVENT CANCELED BEFORE INTIIAL DELAY FIRED')
            return
        
        try:    
            i = 0        
            async for x in generator: 

                ...

                if not (max_iterations is None):
                    i = i+1
                    if i >= max_iterations:
                        raise MaxIteratonsError('')
        
        except MaxIteratonsError:
            print('EVENT HAS HIT MAX ITERATIONS')
        
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

    def close(self, reason = None, finish_func:bool=None):
        self.continue_execution = False
        if self.timer is None: return
        self.reason = reason
        if finish_func is not None:
            _fin = self.finish_func
            self.finish_func = finish_func
            self.timer.cancel()
            self.finish_func = _fin
        else:
            self.timer.cancel()
        self.reason = None
        
    
    async def aclose(self, finalize:bool = False):
        self.close(finalize=finalize)



class Scheduled_Task_Pool():
    unique_tasks : dict
    anon_tasks   : list

    def __init__(self):
        self.unique_tasks = {}
        self.anon_tasks   = []
        self._created     = []
            #debug list, check on del if it has any unstarted or unattached.

    def attach_and_run(self,scheduled_task,interval,start_delay=None,UID=None, max_iterations=None):
        if scheduled_task in self.created:
            self._created.remove(scheduled_task)
        if UID:
            assert not (UID in self.unique_tasks.keys())
            self.unique_tasks[UID] = scheduled_task
        else:
            self.anon_tasks.append(scheduled_task)
        
        task = scheduled_task.task(interval = interval, start_delay=start_delay, max_iterations=max_iterations)
        
    def run_task(self, task:CoroutineType):
        asyncio.create_task(task)

    def close_all(self,reason=None,finish_func=True):
        for scheduled_task in (*self.unique_tasks.values(),*self.anon_tasks):
            scheduled_task.close(reason=reason,finish_func=finish_func)


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
