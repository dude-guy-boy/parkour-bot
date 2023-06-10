# def help(argument):
#     def decorator(function):
#         def wrapper(*args, **kwargs):
#             print("Something")
#             return 0
#         return function
#     return function

# def help(func):
#     def wrapper(*args, **kwargs):
#         print("Decorator 2")
#         return func(*args, **kwargs)
#     return wrapper

# from functools import wraps
# from interactions import SlashCommand, SlashContext, Extension
# import importlib.util, glob
# from pathlib import Path
# from os.path import relpath

# # def help(description: str):
# #     def decorator(func):
# #         async def wrapper(extension: Extension, ctx: SlashContext):
# #             # extension.commands[1].call_callback(extension.commands[1].callback())
# #             for command in extension.commands:
# #                 command: SlashCommand = command
# #                 # await command.call_callback(ctx=ctx)

# #                 print(command.name, command.call_with_binding(callback=command.callback))
# #             print(f"Decorator with argument: {description}")
# #             return description
# #         return wrapper
# #     return decorator
# class storeHelp:
#     list = []

# def process_help(description: str):
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             # Do stuff
#             print(description)
#             storeHelp.list.append(description)
#             return await func(*args, **kwargs)
#         return wrapper
#     return decorator

# def help(description: str):
#     def decorator(func):
#         return process_help(description)(func)
#     return decorator

# def execute_decorator_against_classes():
#     extensions = [{"name": path.stem, "ext-path": relpath(path=path, start="./").replace("/", ".")[:-3], "path": str(path.resolve())} for path in Path("./extensions").rglob("*.py") if path.name not in ("__init__.py", "template.py")]

#     for ext in extensions:
#         print(ext)
#         spec = importlib.util.spec_from_file_location(ext['ext-path'],
#                                                       ext['path'])
#         foo = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(foo)