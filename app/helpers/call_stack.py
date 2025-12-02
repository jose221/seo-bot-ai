import inspect


def get_call_stack():
    # Get the call stack
    stack = inspect.stack()

    # Use map to apply the lambda function to each item in stack, then convert the result to a list
    functions = list(map(lambda x: x.function, stack))

    # Join the list of functions into a single text string
    functions_text = "|".join(reversed(functions))

    return functions_text
