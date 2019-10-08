import PyInstaller
import argparse

if float(PyInstaller.__version__[0]) >= 4:
    from PyInstaller.depend.imphook import ModuleHook
else:
    from PyInstaller.building.imphook import ModuleHook

import PyInstaller.__main__
from os import path, scandir, walk, remove
import shutil
import sys

# constants
WORK_DIR = path.abspath(path.dirname(__file__))
PACKAGE_PATH = path.abspath(path.join(WORK_DIR, ".."))
HOOKS_DIR = path.join(WORK_DIR, "custom_hooks")

PATCH_HOOKS = [path.join(HOOKS_DIR, f.name) for f in scandir(HOOKS_DIR)
               if f.name != "__init__.py"]

patched = set()

# monkey patch hooks
def patched_load_hook_module(self):
    global patched

    for ph in PATCH_HOOKS:
        phb = path.basename(ph)
        if path.basename(self.hook_filename) == phb and phb not in patched:
            print(f"patching hook: --> {self.hook_filename}\n"
                  f"               <-- {ph}")

            self.hook_filename = ph
            patched.add(phb)
            break

    original_load_hook_module(self)


def input_parser():
    """ Parse command line input parameters. """

    parser = argparse.ArgumentParser(description="script to build freezed app")
    parser.add_argument("mode", type=str, help="choose CLI/GUI build mode",
                        choices=["gui", "cli"])
    args = parser.parse_args()

    return args.mode.upper()

# monkey patch hooks
original_load_hook_module = ModuleHook._load_hook_module
ModuleHook._load_hook_module = patched_load_hook_module

# ordered by size
exclude_libs = [
    "tcl",
    "tk",
    "setuptools",
    "pydoc_data",
    "pkg_resources",
    "lib2to3",
    "tkinter",
    "multiprocessing",
    "concurrent",
    "xmlrpc",
    "pywin",
    "Include",
    "curses",
    # "html",  needed by wikipedia
    # "soupsieve",  needed by wikipedia
    # "chardet",  needed by wikipedia
    # "email",  needed by wikipedia
    # "idna",  needed by wikipediaň
    # "http",  needed by wikipedia
    # "xml", needed by nltk
    # "unittest", needed by nltk
    # "sqlite3", needed by nltk
]

# common installer options
installer_opt = [
    # constnts build options
    "--clean",
    "--noconfirm",
    #"--noupx",
    #"--upx-dir=<DIR>",
    #"--version-file=<FILE>",

    # debbugging options
    #"--debug=bootloader",
    #"--debug=all",
    #"--debug=noarchive",

    # pyinstaller data paths and hooks
    f"--paths={PACKAGE_PATH}",
    f"--add-data={path.join(PACKAGE_PATH, 'wiki_music', 'files')};files",
    f"--icon={path.join(PACKAGE_PATH, 'wiki_music', 'files', 'icon.ico')}",
    f"--specpath={WORK_DIR}",
    "--additional-hooks-dir=hooks",
    f"--runtime-hook={path.join(WORK_DIR, 'rhooks', 'pyi_rth_nltk.py')}",

    # what to build
    "--onedir",
    #"--onefile",
    "--name=wiki_music"
]

# installer options specific to gui or cli
if input_parser() == "GUI":
    installer_opt.extend([
        "--distpath=gdist",
        "--windowed",
        f"--add-data={path.join(PACKAGE_PATH, 'wiki_music', 'data')};data",
        f"{path.join(PACKAGE_PATH, 'wiki_music', 'app_gui.py')}"
    ])
else:
    installer_opt.extend([
        "--distpath=cdist",
        "--console",
        f"{path.join(PACKAGE_PATH, 'wiki_music', 'app_cli.py')}"
    ])
    exclude_libs.append("PyQt5")
    exclude_libs.append("distutils")

# prepend the right keyword argument
exclude_libs = [f"--exclude-module={lib}" for lib in exclude_libs]

# join together options together
installer_opt.extend(exclude_libs)

# run build
PyInstaller.__main__.run(installer_opt)

# remove *.pyo bytecompiled files
for root, dirs, files in walk(PACKAGE_PATH):
    for f in files:
        if f.endswith(".pyo"):
            remove(path.join(root, f))

