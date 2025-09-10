import asyncio

class Scheduled_Task():
    
    continue_running = True

    def start(self):
        self.current_generator_coroutine = self.create_async_generator_coroutine()

    def run(self,):
        asyncio.create_task(self.current_generator_coroutine)

    def create_async_generator_coroutine(self):
        return self._run_generator(self._loop())

    async def _loop(self):
        while self.continue_running:
            await self._tick()
            yield

    async def _tick(self):
        print('TICK CALLED')
        await asyncio.sleep(1)

    async def _run_generator(self, generator, max_loops = 3):
        i = 0
        async for item in generator: 
            i = i + 1
            if i >= max_loops:
                self.continue_running = False
        return

async def main():
    a = Scheduled_Task()
    a.start()
    a.run()
    await asyncio.sleep(10)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()