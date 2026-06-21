import importlib
import pkgutil
import os

preloaded_commands = {}
preloaded_handlers = {}

def preload_commands():
    global preloaded_commands, preloaded_handlers
    base_path = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([base_path]):
        if module_name == "__init__":
            continue
        module = importlib.import_module(f"endstone_conditional_quests.commands.{module_name}")

        if hasattr(module, 'command') and hasattr(module, 'handler'):
            for cmd, details in module.command.items():
                preloaded_commands[cmd] = details
                preloaded_handlers[cmd] = module.handler

preload_commands()
