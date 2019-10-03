import PyInstaller

if float(PyInstaller.__version__) >= 4:
    from PyInstaller.depend.imphook import ModuleHook
else:
    from PyInstaller.building.imphook import ModuleHook

import PyInstaller.__main__
from os import path, scandir, walk, remove
import shutil
import sys

wd = path.abspath(path.dirname(__file__))
pth = path.abspath(path.join(wd, ".."))
dist = path.join(wd, "dist", "wiki_music")
hooks_dir = path.join(wd, "custom_hooks")

patch_hooks = [path.join(hooks_dir, f.name) for f in scandir(hooks_dir)
               if f.name != "__init__.py"]

patched = set()

# monkey patch hooks
def _load_hook_module(self):
    global patched

    for ph in patch_hooks:
        phb = path.basename(ph)
        if path.basename(self.hook_filename) == phb and phb not in patched:
            print(f"patching hook: --> {self.hook_filename}\n"
                  f"               <-- {ph}")

            self.hook_filename = ph
            patched.add(phb)
            break

    _old_hook(self)

# monkey patch hooks
_old_hook = ModuleHook._load_hook_module
ModuleHook._load_hook_module = _load_hook_module

PyInstaller.__main__.run([
    "--noconfirm",
    "--onedir",
    "--name=wiki_music",
    "--debug=bootloader",
    #"--debug=all",
    "--debug=noarchive",
    f"--icon={path.join(pth, 'wiki_music', 'files', 'icon.ico')}",
    f"--paths={pth}",
    "--console",
    f"--specpath={wd}",
    "--additional-hooks-dir=hooks",
    f"--runtime-hook={path.join(wd, 'rhooks', 'pyi_rth_nltk.py')}",
    # ordered by size
    "--exclude-module=PyQt5",
    "--exclude-module=tcl",
    "--exclude-module=tk",
    "--exclude-module=setuptools",
    "--exclude-module=pydoc_data",
    "--exclude-module=pkg_resources",
    "--exclude-module=distutils",
    "--exclude-module=lib2to3",
    "--exclude-module=tkinter",
    "--exclude-module=multiprocessing",
    "--exclude-module=concurrent",
    "--exclude-module=xmlrpc",
    "--exclude-module=pywin",
    "--exclude-module=Include",
    "--exclude-module=curses",
    #"--exclude-module=html",  needed by wikipedia
    #"--exclude-module=soupsieve",  needed by wikipedia
    #"--exclude-module=chardet",  needed by wikipedia
    #"--exclude-module=email",  needed by wikipedia
    #"--exclude-module=idna",  needed by wikipediaň
    #"--exclude-module=http",  needed by wikipedia
    #"--exclude-module=xml", needed by nltk
    #"--exclude-module=unittest", needed by nltk
    #"--exclude-module=sqlite3", needed by nltk
    f"--add-data={path.join(pth, 'wiki_music', 'files')};files",
    "--clean",
    f"{path.join(pth, 'wiki_music', 'application.py')}"
])

# remove *.pyo bytecompiled files
for root, dirs, files in walk(pth):
    for f in files:
        if f.endswith(".pyo"):
            remove(path.join(root, f))

