class gfaas:
    def __init__(self, run_local = False):
        self.run_local = run_local

    def __call__(self, func):
        # Firstly, we'll save the function body to file
        import marshal

        module_name = "gfaas_module"
        with open(module_name, "wb") as f:
            marshal.dump(func.__code__, f)

        async def inner(*args, **kwargs):
            import json

            # Save input args to files
            saved_args = []
            for i, arg in enumerate(args):
                arg_name = "arg{}".format(i)
                with open(arg_name, "w") as f:
                    json.dump(arg, f)
                saved_args.append(arg_name)

            if self.run_local:
                import types

                # Load func from file
                with open(module_name, "rb") as f:
                    code = marshal.load(f)

                # Load input args
                parsed_args = []
                for arg_name in saved_args:
                    with open(arg_name, "r") as f:
                        arg = json.load(f)
                        parsed_args.append(arg)

                # Invoke
                func = types.FunctionType(code, globals(), "remote")
                return func(*parsed_args)

            else:
                from yapapi.runner import Engine, Task, vm
                from yapapi.runner.ctx import WorkContext
                from datetime import timedelta

                package = await vm.repo(
                    image_hash = "0dd0509197ad6b9f46eec8ba8f28b8b6c8700edc8f5bbc068974e2b4",
                    min_mem_gib = 1.5,
                    min_storage_gib = 2.0,
                )

                async def worker(ctx: WorkContext, tasks):
                    ctx.log("starting")
                    async for task in tasks:
                        ctx.send_file(module_name, f"/golem/input/func")
                        remote_args = []

                        for arg in saved_args:
                            remote_arg = "/golem/input/{}".format(arg)
                            ctx.send_file(arg, remote_arg)
                            remote_args.append(remote_arg)

                        ctx.run(f"python3 /golem/runner.py", f"/golem/input/func", *remote_args)
                        ctx.download_file(f"/golem/output/out", f"out")
                        yield ctx.commit(task)
                        task.accept_task()

                    ctx.log("done")

                init_overhead: timedelta = timedelta(minutes = 3)

                async with Engine(
                    package = package,
                    max_workers = 3,
                    budget = 100.0,
                    timeout = init_overhead + timedelta(minutes = 1),
                    subnet_tag = "testnet",
                ) as engine:
                    async for progress in engine.map(worker, [Task(data = None)]):
                        print("progress=", progress)

        return inner
