if __name__ == '__main__':
    import json
    import marshal
    import types
    import sys

    module_name = sys.argv[1]
    args = sys.argv[2:len(sys.argv)]

    # Load func from file
    with open(module_name, "rb") as f:
        code = marshal.load(f)

    # Load input args
    parsed_args = []
    for arg in args:
        with open(arg, "r") as f:
            arg = json.load(f)
            parsed_args.append(arg)

    # Invoke
    func = types.FunctionType(code, globals(), "remote")
    out = func(*parsed_args)

    # Save to file
    with open("/golem/output/out", "w") as f:
        json.dump(out, f)
