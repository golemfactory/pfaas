from pfaas import remote_fn
import asyncio

@remote_fn()
def partial_sum(xs: [int]) -> int:
    return sum(xs)

def chunks(xs: [int], size: int) -> [int]:
    for i in range(0, len(xs), size):
        yield xs[i:i + size]

async def main(xs: [int], size: int):
    futs = []
    for chunk in chunks(xs, size):
        futs += [partial_sum(chunk)]
    out = sum(await asyncio.gather(*futs))
    exp = sum(xs)
    assert exp == out, f"sums don't match: expected {exp}, got {out}"
    print("sum = {}".format(out))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main(list(range(100)), 25))
    
    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))

