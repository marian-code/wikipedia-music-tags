import importlib
import os


def load_extractors():
    for module in os.listdir(os.path.dirname(__file__)):
        if module == "__init__.py" or module[-3:] != ".py":
            continue

        name = ".{}".format(module[:-3])
        importlib.import_module(name, __name__)
