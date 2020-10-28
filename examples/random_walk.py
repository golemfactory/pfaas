from pfaas import remote_fn
import asyncio

@remote_fn()
def walk_stats(tries: int, barrier: int) -> int:
    import random

    sum = 0
    for _ in range(tries - 1):
        step, pos = 1, 0
        while True:
            if random.random() < 0.5:
                pos -= step
            else:
                pos += step
            if pos >= barrier or pos <= -barrier:
                break
            step += 1
        sum += step
    return sum

async def main(tries: int, barrier: int, repetitions: int):
    sum = 0
    for _ in range(repetitions):
        sum += await walk_stats(tries, barrier)
    average = sum / (repetitions * tries)
    print(f"average steps number: {average}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main(100, 1_000_000, 10))
    
    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))

