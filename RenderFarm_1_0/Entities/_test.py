import asyncio

''' Online Example, modified'''

async def delayed_async_generator(count, delay):
    for i in range(count):
        yield i
        await asyncio.sleep(delay)  # Introduce delay after yielding each item

async def collect_generator_results(async_gen):
    """Collects all yielded values from an async generator into a list."""
    results = []
    async for item in async_gen:
        print (item)
        results.append(item)
    return results

async def main():
    print("Starting generator iteration with internal delay...")
    # async for item in delayed_async_generator(5, 1):  # 5 items, 1 second delay
    #     print(f"Received: {item}")
    t1 = collect_generator_results(delayed_async_generator(5, 1))
    t2 = collect_generator_results(delayed_async_generator(5, 1))
    
    print("Generator iteration with internal delay finished.")
    
    asyncio.create_task(t1)
    asyncio.create_task(t2)

    await asyncio.sleep(10)
    # results = await asyncio.gather(t1,t2)

if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.gather(main(),main())
    