import importlib
import os


def load_extractors():
    for module in os.listdir(os.path.dirname(__file__)):
        if module == "__init__.py" or not module.endswith((".py", ".pyc")):
            continue

        name = ".{}".format(module.rsplit(".", 1)[0])
        importlib.import_module(name, __name__)
