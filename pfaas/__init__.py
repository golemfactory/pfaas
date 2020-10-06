class remote_fn:
    def __init__(self, run_local: bool = False):
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
                arg_name = f"arg{i}"
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
                from yapapi.log import enable_default_logger, log_summary
                from datetime import timedelta

                enable_default_logger()
                package = await vm.repo(
                    image_hash = "74e9cdb5a5aa2c73a54f9ebf109986801fe2d4f026ea7d9fbfcca221",
                    min_mem_gib = 0.5,
                    min_storage_gib = 2.0,
                )

                async def worker(ctx: WorkContext, tasks):
                    async for task in tasks:
                        ctx.send_file(module_name, "/golem/input/func")
                        remote_args = []

                        for arg in saved_args:
                            remote_arg = f"/golem/input/{arg}"
                            ctx.send_file(arg, remote_arg)
                            remote_args.append(remote_arg)

                        ctx.run("python", "/golem/runner.py", "/golem/input/func", *remote_args)
                        ctx.download_file("/golem/output/out", "out")
                        yield ctx.commit()
                        task.accept_task(result="out")

                    ctx.log("done")

                init_overhead: timedelta = timedelta(minutes = 3)

                async with Engine(
                    package = package,
                    max_workers = 3,
                    budget = 100.0,
                    timeout = init_overhead + timedelta(minutes = 10),
                    subnet_tag = "devnet-alpha.2",
                    event_emitter = log_summary(),
                ) as engine:
                    async for progress in engine.map(worker, [Task(data = None)]):
                        print(f"progress={progress}")

                with open("out", "r") as f:
                    out = json.load(f)

                return out

        return inner
