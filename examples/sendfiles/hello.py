from pfaas import remote_fn
import asyncio
import os
import sys
from pathlib import PurePath, Path

from typing import List, Tuple, Optional

local_progpath = os.path.abspath(__file__)
local_progdir = PurePath(local_progpath).parent


@remote_fn(
    run_local=False,
    extrafiles = [
        (local_progdir/'salt.txt', 'salt.txt'),
        (local_progdir/'helpers.py', 'helpers.py')
    ],
    )

def hello(msg: str) -> Tuple[List[str],Optional[str]]:
    progress = []
    try:
        import os
        import sys
        from pathlib import PurePath
        progress.append('std imports OK')
        remote_progpath = os.path.abspath(sys.argv[0])
        remote_progdir = PurePath(remote_progpath).parent
        progress.append(f"progdir: {remote_progdir}")
        sys.path.append(str(remote_progdir/'input'))
        progress.append(f"sys.path: {sys.path}")
        import helpers
        progress.append('helper imports OK')        
        with open(remote_progdir / 'input/salt.txt') as f:
            salt = f.read()
        progress.append(f"salt: {salt}")
        value = helpers.upper(msg, salt)
        progress.append(f"value: {value}")
        return progress, value
    except Exception as e:
        progress.append( f"Exception: {e}")
        return progress, None

async def main(msg: str):
    progress, resp = await hello(msg)
    if resp is None:
        print("Failed:")
        print(*progress,sep="\n")
        return
    
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

