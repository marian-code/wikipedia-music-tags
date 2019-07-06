"""Import all the modules."""
import importlib
import os

imported = []

for module in os.listdir(os.path.dirname(__file__)):
    if module == "__init__.py" or module[-3:] != ".py":
        continue

    name = ".{}".format(module[:-3])
    imported.append(importlib.import_module(name, __name__))
