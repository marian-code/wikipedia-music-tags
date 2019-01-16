# Wikipegia music tags parser

Python application which parses wikipedia for music tags and writes them to 
files. Has also the ability to search for lyrics and album cover art.

## Getting Started

Anyone is welcome to use it or contribute. Project has unfortunately plenty
or requirements of which some might be tricky to install. Most notably pytaglib.
I also use edited versions of [google-images-download](https://github.com/hardikvasa/google-images-download) and [LyricsFinder](https://github.com/GieselaDev/LyricsFinder), but 
those are found in the repository.

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
requests>=2.18.4
pytaglib>=1.4.4
wikipedia>=1.4.0
numpy>=1.14.3
PyQt5>=5.11.3
python-Levenshtein>=0.12.0
```

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
This is best leaved as is otherwise you will have to modify setup scripts for cx_Freeze. But other than this the location doesn´t really matter.

If you want to try and package script you also need to install
```
cx-Freeze>=5.1.1
```

packages that are not necessary:
* *python-Levenshtein* makes fuzzywuzzy a whole lot faster
* *lxml* makes Beautifulsoup a whole lot faster
* *PyQt5* if you want to use Tkinter GUI (deprecated) or console mode

You should be able to seamlessly substitute **PyQt5** with **PySide2** or **PyQt4** just by changing imports and some little alterations to the code.

The module was written so it could run on any platform with python installation. But it is only tested under Windows with Anaconda 5.2.0. With only some minor modifications module should be able to run on Linux and Os X too. This concers mainly default paths and interaction with clipboard in GUI.

If you want to utilize lyrics search you will have to get a [Google Developer API Key](https://console.developers.google.com/projectselector/apis/library/customsearch.googleapis.com/) **(Strongly Recommended)** with the 'Custom Search' API enabled. This link should take one there once logged in. this is a requirement of [LyricsFinder](https://github.com/GieselaDev/LyricsFinder) module. When you have the key create a file named **google_api_key.txt** under **files** directory and copy the key there.

### Installing

There´s no installing yet but the module can be packaged with cx_Freeze 
although it is still moderately buggy.
So to get it just:

```
git clone <repo address>
```
If you don´t want to package the module, skpi to the next section

You can package the script with cx_Freeze but in this stage it is still kind of buggy. If you decide to do so, before the first run of the respective setup script uncomment the line:
```
# generate_excludes()
```
This will generate list of modules to exclude, because cx_Freeze loves to include your whole python instalation. Also change these variables to suit your system:
```
os.environ['TCL_LIBRARY']
os.environ['TK_LIBRARY']
```
If you chose different than default location for nltk data you will have to modify variable
```
nltk_path
```
to your selected location.

After this you can proceed with the packaging.

There are two GUI versions one which uses Tkinter which is now deprecated. It should still be functional but will no longer be maintained. To package 
the module with it:

```
setup.py build
```

The more recent version of the GUI is written in PyQt5. To build it:

```
setup_Qt.py build
```
This version of setup might be still buggy and is under developement

There is a third commandline-only option which is the most stable. To build it:
```
setup_cmd.py build
```

## Running the code

The module can be run from the command line. There are 3 options:
1. command line mode:
```
python application.py
```
2. PyQt5 GUI mode:
```
python gui_Qt.py
```
3. Tkinter GUI mode (deprecated):
```
python gui.py
```
**libb** can also be used as a library for getting music tags, lyrics and writing them to files

## Running the tests

There are no predefined tests at the moment

## Coding style tests

Coding style adheres on PEP8 style guide so just use PEP8 lintner and read the docs.

## Contributing

There are some TODOs scattered around the code and created issues so 
thats a good place to start. Base user interface layout should be changed only with the use of Qt designer and use of files:
```
art_dialog_base.ui
Qt_layout.ui
```
The coresponding python files:
```
art_dialog_base.py
Qt_layout.py
```
are then generated by use of command (applies to *PyQt5* under Windows):
```
pyuic5.exe -x cover_art.ui -o cover_art.py
```
*PyQt4* and *PySide2* have utilities with other names.

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


