<div align="center">
  <h1><code>pfaas</code></h1>

  <p>
    <strong>Function-as-a-Service on top of Golem Network in Python</strong>
  </p>
</div>

This module allows you to distribute heavy-workload functions to the [Golem Network]. This is a
sister project to [gfaas].

[Golem Network]: https://golem.network
[gfaas]: https://github.com/golemfactory/gfaas

⚠️ **Disclaimer:** Use with extra care as this package is highly experimental. ⚠️

## Quick start

Currently, the only supported version of Python is version `3.8`. Additionally, since this package is
not yet released on pypi, you will need to manually install its dependencies

```
pip3 install yapapi
```

The usage is pretty straightforward. In your main Python module, e.g. `main.py`, import `pfaas` and
annotate some heavy-workload function to be distributed on the Golem Network like so

```python
from pfaas import remote_fn
import asyncio

@remote_fn()
def hello(msg: str) -> str:
    return msg.upper()

async def main(msg: str):
    resp = await hello(msg)
    print(f"in={msg}, out={resp}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main("hey there, yagna!"))

    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))
```

Now simply run as usual

```
python3 main.py
```

## Notes about `pfaas.remote_fn`

When you annotate a function with `pfaas.remote_fn` attribute, it gets expanded into a
full-fledged async function. So for instance, the following function

```python
from pfaas import remote_fn

@remote_fn()
def hello(input: str) -> str
```

expands into

```python
async def hello(input: str) -> str
```

Therefore, it is important to remember that you need to run the function in an async block.

## Notes on running your app locally (for testing)

It is well known that prior to launching our app on some distributed network of nodes, it
is convenient to first test the app locally in search of bugs and errors. This is also
possible with `pfaas`. In order to force your app to run locally, simply pass `run_local = True`
as argument to `pfaas.remote_fn` decorator

```python
from pfaas import remote_fn

@remote_fn(run_local = True)
def hello(msg: str) -> str
```

## Examples

A couple illustrative examples of how to use this module can be found in the `examples/`
directory.
