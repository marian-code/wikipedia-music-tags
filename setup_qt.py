"""
This is the setup script for the Wiki Music module.\n
The script creates a standalone windows executable.
"""


import sys
from cx_Freeze import setup, Executable
import os
import shutil
import logging
import distutils


def generate_excludes():
    # python modules install dir
    path = (r"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Anaconda3_64\Lib\site-packages")

    dirs = []
    for d in os.listdir(path):
        # print(os.path.isdir(os.path.join(d)))
        if (os.path.isdir(os.path.join(path, d)) and "egg" not in d and
           "info" not in d):

            dirs.append(d)

    with open(r"files\excludes_qt.txt", "w") as infile:
        for d in dirs:
            infile.write(d + "\n")


def main():

    # append to path so wiki_music can be imported
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    # set tcl paths
    #TODO apparently we dont need tcl lib but cx_freeze is unhappy without them
    os.environ['TCL_LIBRARY'] = r"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Anaconda3_64\tcl\tcl8.6"
    os.environ['TK_LIBRARY'] = r"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Anaconda3_64\tcl\tk8.6"

    # packages we want to import
    packages = [
        "bs4",
        "codecs",
        "collections",
        "colorama",
        "ctypes",
        "datefinder",
        "datetime",
        "fuzzywuzzy",
        "functools",
        "json",
        "lazy_import",
        "Levenshtein",
        "multiprocessing",
        "nltk",
        "os",
        "pickle",
        "re",
        "requests",
        "subprocess",
        "sys",
        "taglib",
        "threading",
        "time",
        "unicodedata",
        "warnings",
        "webbrowser",
        "wikipedia",
        # lyricsfinder
        "lyricsfinder",
        "logging",
        "typing",
        "importlib",
        "io",
        "lyricsfinder.extractors.darklyrics",
        "lyricsfinder.extractors.genius",
        # app
        "wiki_music",
        "__init__",
        "application",
        "libb.ID3_tags",
        "libb.lyrics",
        "libb.wiki_parse",
        "package_setup",
        "utils",
        # for wikipedia
        "urllib3",
        "chardet",
        "certifi",
        "idna",
        # datefinder
        "dateutil",
        # bs4
        "lxml",
        #
        "numpy",
        # debugg
        "logging",
    ]

    # define variables
    GUI = True
    optimize = 0  # 0, 1, 2
    app_name = 'Wiki_Music.exe'
    # !This only needs to run for the first time
    # generate_excludes()

    with open("README", 'r') as f:
        long_description = f.read()

    with open(r"files\excludes_qt.txt", "r") as f:
        excludes = f.read()

    excludes = excludes.split("\n")

    # setups and test files
    excludes.append("setup")
    excludes.append("test")
    excludes.append("parallel")
    excludes.append("shared_parallel_string")
    excludes.append("code_evolution")
    excludes.append("gui")
    # TODO not complete

    # include files
    include_files = [(os.path.join(os.path.dirname(__file__),
                      "files/icon.ico"),
                      "files/icon.ico")]

    if GUI is True:

        # GUI applications require a different base on Windows
        if sys.platform == "win32":
            base = "Win32GUI"
        executable = "gui_Qt.py"
        description = """Wiki Music - simple Tkinter GUI app that
                         parses Wikipedia for music metadata"""
    else:
        excludes.append("gui_Qt")
        excludes.append("gui_Qt_base")
        excludes.append("PyQt5")
        excludes.append("gui")

        base = "Console"
        executable = "application.py"
        description = """Wiki Music - console app that parses Wikipedia
                         for music metadata"""

    excludes = [ex for ex in excludes if ex not in packages]
    excludes.remove("PyQt5")

    build_exe_options = {"packages": packages,
                         "excludes": excludes,
                         'zip_include_packages':'PyQt5',
                         "includes": [
                             "lyricsfinder",
                             "PyQt5.QtCore",
                             "PyQt5.QtGui",
                             "PyQt5.QtWidgets",
                             "PyQt5.sip"],
                         "optimize": optimize,
                         "include_files": include_files}

    setup(name="wiki_music",
          version="1.0",
          license="MIT",
          long_description=long_description,
          author='Marián Rynik',
          author_email='marian.rynik@outlook.sk',
          url=" ",
          description=description,
          # packages=['wiki_music'],  #same as name
          # install_requires=packages, #external packages as dependencies
          options={"build_exe": build_exe_options},
          executables=[Executable(executable,
                                  base=base,
                                  targetName=app_name,
                                  icon='files/icon.ico')])

if __name__ == "__main__":

    # loggging for app
    formatter = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
                                  "pid = %(process)d \n\t - "
                                  "proces name = %(processName)s \n\t - "
                                  "module = %(module)s,"
                                  "funcName = %(funcName)s \n\t - "
                                  "%(message)s \n\t",
                                  datefmt="%H:%M:%S")

    log_setup = logging.getLogger('wiki_music_setup')
    log_setup.setLevel(logging.DEBUG)
    fh = logging.FileHandler('wiki_music_setup.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log_setup.addHandler(fh)

    main()

    # define paths
    nltk_path = r"C:\nltk_data"
    build_path = os.path.join(os.path.dirname(__file__), "build")

    print("\nCleaning up unnecessary files...\n")
    remove_dirs = ["build",
                   "logs",
                   "Queen Of Time",
                   "test_music",
                   "tests",
                   ".vscode"]

    for root, dirs, files in os.walk(build_path):
        for d in dirs:
            if "wiki_music" in d:
                try:
                    for r in remove_dirs:
                        print("removing:", os.path.join(root, d, r))
                        shutil.rmtree(os.path.join(root, d, r))

                    print("removing:",
                          os.path.join(root, d, "wiki_music_setup.log"))
                    os.remove(os.path.join(root, d, "wiki_music_setup.log"))
                except FileNotFoundError as e:
                    print(e)
            if "logs" in d:
                try:
                    shutil.rmtree(os.path.join(root, d))
                except FileNotFoundError as e:
                    print(e)

    print("\nCopying necessary nltk data...\n")

    copy_dirs = ["corpora\\words",
                 "chunkers\\maxent_ne_chunker",
                 "taggers\\averaged_perceptron_tagger"]
    copy_files = ["corpora\\stopwords\\english",
                  "tokenizers\\punkt\\english.pickle",
                  "tokenizers\\punkt\\PY3\\english.pickle"]
    mk_dirs = ["tokenizers\\punkt\\PY3", "corpora\\stopwords"]

    # copy whole dirs
    for d in copy_dirs:
        print("copying dir:", os.path.join(nltk_path, d), "\nto:",
              os.path.join(build_path, "exe.win-amd64-3.6\\nltk_data", d))
        try:
            shutil.copytree(os.path.join(nltk_path, d),
                            os.path.join(build_path,
                                         "exe.win-amd64-3.6\\nltk_data",
                                         d))
        except FileExistsError as e:
            print(e)

    # create new dirs so files can be copied
    for m in mk_dirs:
        try:
            os.makedirs(os.path.join(build_path,
                                     "exe.win-amd64-3.6\\nltk_data",
                                     m))
        except FileExistsError as e:
            print(e)

    # copy individual files
    for f in copy_files:
        print("copying file:", os.path.join(nltk_path, f), "\nto:",
              os.path.join(build_path, "exe.win-amd64-3.6\\nltk_data", f))
        try:
            shutil.copy(os.path.join(nltk_path, f),
                        os.path.join(build_path,
                                     "exe.win-amd64-3.6\\nltk_data",
                                     f))
        except FileExistsError as e:
            print(e)

    print("\nDone!")
