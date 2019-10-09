# Wikipegia music tags parser

[![license](https://img.shields.io/pypi/l/qtpy.svg)](./LICENSE)
[![Documentation Status](https://readthedocs.org/projects/wikipedia-music-tags/badge/?version=latest)](https://wikipedia-music-tags.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/marian-code/wikipedia-music-tags/badge.svg?branch=master)](https://coveralls.io/github/marian-code/wikipedia-music-tags?branch=master)

Python application which parses wikipedia for music tags and writes them to 
files. Has also the ability to search for lyrics and album cover art.

## Getting Started

The docs can be found at [readthedocs](https://wikipedia-music-tags.readthedocs.io/en/latest/index.html). They are still under construction!

Anyone is welcome to use it or contribute. All of the dependencies are fairly common so you shouldn't encounter any problems.
I also use edited versions of [google-images-download](https://github.com/hardikvasa/google-images-download) and [LyricsFinder](https://github.com/GieselaDev/LyricsFinder), but 
those are found in the repository. Curentlly supported versions of python are 3.6 and 3.7.

### Prerequisites

These are the modules you have to install first:

```
beautifulsoup4>=4.6.0
colorama>=0.4.0
datefinder>=0.6.1
fuzzywuzzy>=0.17.0
lazy-import>=0.2.2
lxml>=4.2.1
nltk>=3.3
mutagen>=1.42.0
numpy>=1.14.3
Pillow>=6.2.0
pyyaml>=5.1.2
PyQt5>=5.11.3
python-Levenshtein>=0.12.0
QtPy>=1.7.0
requests>=2.18.4
wikipedia>=1.4.0
```

Multiple Qt backends are supported with the help of QtPy. So you can substitute 
PyQt5 for: PyQt4, PySide2 or PySide. However, for now only compatibility with 
PyQt5 is tested, so naturally it is also recomended.

Versions that are equal to listed vesions are tested. Higher vesions should work but are not guaranted to. All modules are found in PyPI so installing should be as easy as:
```
pip install -r requirements.txt
```

You will also need to download nltk data. To do this open console and start python interpreter by typing:
```
python
```
or (if you have anaconda instalation for example)
```
ipython
```
then
```
import nltk
nltk.download()
```
After this a window will open. In the collections tab download **popular**. Default location under Windows is:
```
C:\nltk_data
```
This is best leaved as is.

If you want to try and package script you also need to install pyinstaller.
```
pip install pyinstaller>=3.5
```

packages that are not necessary:
* *python-Levenshtein* makes fuzzywuzzy a whole lot faster
* *lxml* makes Beautifulsoup a whole lot faster
* *PyQt5* if you want to use console mode or other Qt backend

The module was written so it could run on any platform with python installation. But it is only tested under Windows 10 with Anaconda 5.2.0. With only some minor modifications it should be able to run on Linux and Os X too. Problems concern mainly default paths and interaction with clipboard in GUI.

If you want to utilize lyrics search you will have to get a [Google Developer API Key](https://console.developers.google.com/projectselector/apis/library/customsearch.googleapis.com/) **(Strongly Recommended)** with the 'Custom Search' API enabled. The link should take one there once logged in. This is a requirement of [LyricsFinder](https://github.com/GieselaDev/LyricsFinder) module. When you have the key create a file named **google_api_key.txt** under **files** directory and copy the key there.

### Installing

There´s no installing yet but the module can be packaged with pyinstaller 
although it is still considerably buggy.

If you want to just get the script:

```
git clone <repo address>
```
If you don´t want to package the module, skip to the next section.

If you decide to package the script: (for now only **console** version packaging is working)

If you have installed pyinstaller the steps are following:
I **strongly recomend** that you create a virtual environment before proceeding,
with only requirements needed for this project. Otherwise pyinstaller will
bundle too many useless libraries in frozen app. The freezed app size can easily
get over 1GB then. For the same reasons Anaconda installation is even worse
because it has so many libraries by default. If for some strange reason you don't want to
create virtual env you can use option 
```
--exclude-module=
```
in freeze.py to exclude unwanted libraries. In python virtual environment can be
created and activated by:
```
python3 -m venv /path/to/new/virtual/environment
source <venv>/bin/activate (Posix)
<venv>\Scripts\activate.bat (Windows)
```
in Anaconda (env with pip):
```
conda create --prefix /path/to/new/virtual/environment pip
conda activate /path/to/new/virtual/environment
```
Once you have done that there is one optional optimization. You can use 'vanilla'
numpy to further reduce size of freezed app. Vanilla numpy build can be downloaded
from here: [numpy vanilla](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy). The problem with regular numpy is building against OPENBLAS (pip version ~40MB) or Intel MKL (Anaconda version ~ 300MB). Once you've downloaded wheel package for your python version, install it by:
```
pip install <package-name>.whl
```
Now you are ready to go, change to dir:
```
cd setup/
```
and build by:
```
python freeze.py
```
When building in virtual env the frozen app should have ~ 75MB. Without vanilla numpy ~105MB.

This will generate list two directories under setup/ folder: dist/ and build/.
build contains just pyinstaller help files and **dist/wiki_music** contains 
packaged console app. 

There is no building for GUI versionn yet.

## Running the code

The module can be run from the command line. There are 2 options:
1. command line mode:
```
python app_cli.py
```
2. PyQt5 GUI mode:
```
python app_gui.py
```

**library** can also be used as a library for getting music tags, lyrics and writing them to files

## Running the tests

Tests are in early development stage. Make sure all tests in tests dir pass. For now we still heavily rely on exploratory testing

## Coding style tests

Coding style adheres on PEP8 style guide so just use PEP8 lintner and read the docs. 
We also use type anotations together with mypy static typechecking.

## Contributing

There are some TODOs scattered around the code and created issues so thats a good place to start. 
There is also a list of TODOs maintained in 
[code_changelog](https://github.com/marian-code/wikipedia-music-tags/blob/master/code_changelog.md) file. 
Base user interface layout should be changed only with the use of Qt designer and use of files:
```
art_dialog_base.ui
Qt_layout.ui
cover_art_base.ui
```
The coresponding python files:
```
art_dialog_base.py
Qt_layout.py
cover_art_base.py
```
are then generated by use of command (applies to *PyQt5* under Windows):
```
pyuic5.bat -x cover_art.ui -o cover_art.py
```
*PyQt4*, *PySide2* and *PySide* have utilities with other names.

Changes to the code before git are in code changelog file.

## Authors

* **Marián Rynik** - *Initial work* - [marian-code](https://github.com/marian-code)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

None yet.

## Acknowledgments

* Stackoverflow
* [Giesela Inc.](https://github.com/GieselaDev) - LyricsFinder
* [https://github.com/hardikvasa](https://github.com/hardikvasa) - google_images_download


