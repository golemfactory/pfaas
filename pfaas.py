class gfaas:
    def __init__(self, run_local = False):
        self.run_local = run_local

    def __call__(self, func):
        # Firstly, we'll save the function body to file
        import marshal

        with open("gfaas_module", "wb") as f:
            marshal.dump(func.__code__, f)

        async def inner(*args, **kwargs):
            import types
            import json

            # Save input args to files
            for i, arg in enumerate(args):
                with open("arg{}".format(i), "w") as f:
                    json.dump(arg, f)

            if self.run_local:
                # Load func from file
                with open("gfaas_module", "rb") as f:
                    code = marshal.load(f)

                # Load input args
                parsed_args = []
                for fn in ["arg{}".format(i) for i in range(len(args))]:
                    with open(fn, "r") as f:
                        arg = json.load(f)
                        parsed_args.append(arg)

                # Invoke
                func = types.FunctionType(code, globals(), "remote")
                return func(*parsed_args)

            else:
                # TODO add Golem glue code
                raise NotImplementedError("Yagna glue code not implemented yet!")

        return inner
