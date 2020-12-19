import json
from datetime import timedelta
import tempfile
from pathlib import PurePath
import marshal


def _local_remote_fn(module_path, *args):
    import marshal
    import types

    # Load func from file
    with open(module_path, "rb") as f:
        code = marshal.load(f)

    # Invoke
    func = types.FunctionType(code, globals(), "remote")
    return func(*args)


class remote_fn:
    def __init__(
            self,
            run_local: bool = False,
            budget: float = 10.0,
            timeout: timedelta = timedelta(minutes=10),
            subnet: str = "community.3",
            max_workers: int = 2,
        ):
        self.run_local = run_local
        self.budget = budget
        self.timeout = timeout
        self.subnet = subnet

        if run_local:
            from concurrent.futures import ProcessPoolExecutor
            self.engine = ProcessPoolExecutor(max_workers=max_workers)

    def __del__(self):
        if self.run_local:
            self.engine.shutdown()

    def __call__(self, func):
        async def inner(*args, **kwargs):
            # Firstly, we'll save the function body to file
            tmpdir = tempfile.TemporaryDirectory()
            module_path = PurePath(f"{tmpdir.name}/gfaas_module")
            with open(module_path, "wb") as f:
                marshal.dump(func.__code__, f)

            if self.run_local:
                import asyncio

                fut = self.engine.submit(_local_remote_fn, module_path, *args)
                res = await asyncio.wait_for(asyncio.wrap_future(fut), self.timeout.seconds)
                return res

            else:
                from yapapi import Executor, Task, WorkContext
                from yapapi.log import enable_default_logger, log_summary, log_event_repr
                from yapapi.package import vm

                # Save input args to files
                saved_args = []
                for i, arg in enumerate(args):
                    arg_path = PurePath(f"{tmpdir.name}/arg{i}")
                    with open(arg_path, "w") as f:
                        print(arg)
                        json.dump(arg, f)
                    saved_args.append(arg_path)

                enable_default_logger()
                package = await vm.repo(
                    image_hash = "74e9cdb5a5aa2c73a54f9ebf109986801fe2d4f026ea7d9fbfcca221",
                    min_mem_gib = 0.5,
                    min_storage_gib = 2.0,
                )
                out_path = PurePath(f"{tmpdir.name}/out")

                async def worker(ctx: WorkContext, tasks):
                    async for task in tasks:
                        ctx.send_file(module_path, "/golem/input/func")
                        remote_args = []

                        for (i, arg_path) in enumerate(saved_args):
                            print(i, arg_path)
                            remote_arg = f"/golem/input/arg{i}"
                            ctx.send_file(arg_path, remote_arg)
                            remote_args.append(remote_arg)

                        ctx.run("python", "/golem/runner.py", "/golem/input/func", *remote_args)
                        ctx.download_file("/golem/output/out", out_path)
                        yield ctx.commit()
                        task.accept_result(result=out_path)

                    ctx.log("done")

                init_overhead: timedelta = timedelta(minutes = 3)

                async with Executor(
                    package = package,
                    max_workers = 1,
                    budget = self.budget,
                    timeout = init_overhead + self.timeout,
                    subnet_tag = self.subnet,
                    event_consumer = log_summary(),
                ) as executor:
                    async for progress in executor.submit(worker, [Task(data = None)]):
                        print(f"progress={progress}")

                with open(out_path, "r") as f:
                    out = json.load(f)

                return out
        return inner
