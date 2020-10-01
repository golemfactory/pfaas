def gfaas(func):
    # Firstly, we'll save the function body to file
    import marshal

    with open("gfaas_module", "wb") as f:
        marshal.dump(func.__code__, f)

    def inner(*args, **kwargs):
        import types

        # TODO add Golem glue code
        with open("gfaas_module", "rb") as f:
            code = marshal.load(f)
        
        func = types.FunctionType(code, globals(), "remote")
        return func(*args, **kwargs)

    return inner
