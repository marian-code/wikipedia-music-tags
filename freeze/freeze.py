"""Freezes wiki_music into standalone executable."""

import argparse
import logging
import shutil
import sys
from multiprocessing import Process
from pathlib import Path
from typing import List, Set
from zipfile import ZipFile

import PyInstaller
import PyInstaller.__main__

if float(PyInstaller.__version__[0]) >= 4:
    from PyInstaller.depend.imphook import ModuleHook  # pylint: disable=no-name-in-module, import-error
else:
    from PyInstaller.building.imphook import ModuleHook


# constants
WORK_DIR = Path(".")
PACKAGE_PATH = WORK_DIR.parent
WIKI_MUSIC = PACKAGE_PATH / 'wiki_music'
HOOKS_DIR = WORK_DIR / "custom_hooks"

PATCH_HOOKS = [f for h in HOOKS_DIR.glob("*.py") if f.name != "__init__.py"]

patched: Set[str] = set()


def patched_load_hook_module(self):
    """Monkey pytch PyInstaller hooks, with ones from custom_hooks dir."""
    global patched

    for p in PATCH_HOOKS:
        if Path(self.hook_filename).name == p.name and p.name not in patched:
            print(f"patching hook: --> {self.hook_filename}\n"
                  f"               <-- {p}")

            self.hook_filename = p
            patched.add(p.name)
            break

    original_load_hook_module(self)


def input_parser():
    """Parse command line input parameters."""
    parser = argparse.ArgumentParser(description="script to build freezed app")
    parser.add_argument("mode", type=str, help="choose CLI/GUI build mode",
                        choices=["gui", "cli", "all"])
    parser.add_argument("-p", "--package", type=bool, action="store_true",
                        help="package to zip for release", default=False)
    args = parser.parse_args()

    return args.mode.upper(), args.package


def set_loggers():
    """Setup loggers for freezing."""
    for name in logging.root.manager.loggerDict:
        log = logging.getLogger(name)

        if name == "PyInstaller":
            fh = logging.FileHandler("freeze_build.log", mode="w")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(levelname)s - %(module)s - "
                                              "%(message)s"))
            log.addHandler(fh)


def clear_path(mode: str):
    """Remove all files and dirs from the build path prior to freezing.

    Parameters
    ----------
    mode: str
        build GUI or CLI or both
    """
    if mode == "GUI" or mode == "ALL":

        try:
            shutil.rmtree("gdist")
        except FileNotFoundError:
            pass
        except OSError as e:
            print(e)
            sys.exit()
    elif mode == "CLI" or mode == "ALL":
        try:
            shutil.rmtree("cdist")
        except FileNotFoundError:
            pass
        except OSError as e:
            print(e)
            sys.exit()


def build(mode: str, installer_opt: List[str], exclude_libs: List[str],
          package: bool):
    """Sets the correct arguments based on mode and freezes the app.

    Parameters
    ----------
    mode: str
        GUI, CLI aor ALL
    installer_opt: list
        list of pyinstaller options
    exclude_libs
        list of libraries for pyinstaller to exclude
    """
    # installer options specific to gui or cli
    if mode == "GUI":
        build_path = WORK_DIR / "gdist" / "wiki_music"
        zip_file = WORK_DIR /"wiki_music_gui.zip"

        installer_opt.extend([
            "--distpath=gdist",
            "--windowed",
            f"--add-data={WIKI_MUSIC / 'data')};data",
            f"--add-data={WIKI_MUSIC / 'ui')};ui",
            f"{WIKI_MUSIC / 'app_gui.py')}"
        ])
    else:
        build_path = WORK_DIR / "cdist" / "wiki_music"
        zip_file = WORK_DIR / "wiki_music_cli.zip"

        installer_opt.extend([
            "--distpath=cdist",
            "--console",
            f"{WIKI_MUSIC / 'app_cli.py')}"
        ])
        exclude_libs.append("PyQt5")
        exclude_libs.append("distutils")

    # prepend the right keyword argument
    exclude_libs = [f"--exclude-module={lib}" for lib in exclude_libs]

    # join together options together
    installer_opt.extend(exclude_libs)

    # run build
    PyInstaller.__main__.run(installer_opt)

    # package files for release
    with ZipFile(zip_file, "w") as zf:
        for f in build_path.rglob("*"):
            zf.write(f)


# get build mode and packaging choice
mode, package = input_parser()

# clear build paths
clear_path(mode)

# setup loggers
set_loggers()

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
    # ? constnts build options
    "--clean",
    "--noconfirm",
    # "--version-file=<FILE>",

    # ? debbugging options
    # "--debug=bootloader",
    # "--debug=all",
    # "--debug=noarchive",

    # ? upx options
    "--noupx",
    "--upx-exclude=vcruntime140.dll",
    "--upx-exclude=msvcp140.dll",
    "--upx-exclude=qwindows.dll",
    "--upx-exclude=qwindowsvistastyle.dll",
    f"--upx-dir={WORK_DIR / 'upx')}",

    # ? pyinstaller data paths and hooks
    f"--paths={PACKAGE_PATH}",
    f"--add-data={WIKI_MUSIC / 'files')};files",
    f"--icon={WIKI_MUSIC / 'files' / 'icon.ico')}",
    f"--specpath={WORK_DIR}",
    "--additional-hooks-dir=hooks",
    f"--runtime-hook={WORK_DIR / 'rhooks' / 'pyi_rth_nltk.py')}",

    # ? what to build
    "--onedir",
    # "--onefile",
    "--name=wiki_music",
]

# run build
if mode in ("CLI", "GUI"):
    build(mode, installer_opt, exclude_libs, package)
elif mode == "ALL":
    gui = Process(target=build, name="GUI", daemon=True,
                  args=("GUI", installer_opt, exclude_libs, package))
    cli = Process(target=build, name="CLI", daemon=True,
                  args=("GUI", installer_opt, exclude_libs, package))

    cli.join()
    gui.join()

# remove *.pyo bytecompiled files
for f in PACKAGE_PATH.rglob("*.pyo"):
    f.unlink()
