from pfaas import gfaas
import asyncio

@gfaas
def hello(msg):
    return msg.upper()

async def main(msg):
    await asyncio.sleep(1)
    resp = await hello(msg)
    print("in={}, out={}".format(msg, resp))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main("hey there, yagna!"))
    
    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))

