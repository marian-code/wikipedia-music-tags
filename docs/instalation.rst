Installation instructions
=========================

Common instructions
-------------------

.. warning:: 
    Documentation is stil under construction some things might not be up to
    date.

.. note:: 
    If you are a user and don't want to bother yourself you can skip to
    `For Users`_. The application will be 100% functional although the
    extraction won't be as effective. All these problems will disappear in the
    next version once the package is pip installable.

If you want to utilize full power of lyrics search you will have to get a
`Google Developer API Key <https://console.developers.google.com/projectselector/apis/library/customsearch.googleapis.com/>`_
**(Strongly Recommended)** with the 'Custom Search' API enabled. The link
should take one there once logged in. This is a requirement of
`LyricsFinder <https://github.com/GieselaDev/LyricsFinder>`_ module.
When you have the key create a file named **google_api_key.txt** under
**files** directory in package root folder and copy the key there.

For improved artist detection it is also recommended to download appropriate
nltk data. Before this step you should have nltk library installed.
So you can install the project following **user** or **developer** instructions
and then proceed. Open console and start python interpreter by typing:

.. code-block:: bash

    python

or (if you have anaconda instalation for example)

.. code-block:: bash
    
    ipython

then

.. code-block:: python

    import nltk
    nltk.download()

After this a window will open. In the collections tab download **popular**.
Default location under Windows is: ``C:\nltk_data`` This is best leaved as is.


For Users
---------

We aim to have pip installable module in 0.4.0-alpha that is only one release
away. For now you must install manually using setup.py. Beware! there are still some
problems, mainly log dirrectory management which will require app to run
in elevated privilages mode because it writes logs in its install directory.
So for now if you want to install:

.. code-block:: bash

    git clone git@github.com:marian-code/wikipedia-music-tags.git
    cd wikipedia-music-tags
    pip install -r requirements.txt
    python setup.py install

Instalation creates two entry points which can be run from command line, one
for GUI and one for CLI version.

.. code-block:: bash

    wiki_music_gui(.exe)
    wiki_music_cli(.exe)

For Developers
--------------

.. note::
    It is strongly recommended to create a virtual environment for development,
    expecially if you intend to build frozen app. See section
    `Creating virtual environment`_

For basic setup just clone from git and install requirements.

The module was written so it could run on any platform with python
installation. But it is only tested under Windows 10 with Anaconda 5.2.0.
With only some minor modifications it should be able to run on Linux and
Os X too. Problems concern mainly default paths and interaction with
clipboard in GUI.

Multiple Qt backends are supported with the help of QtPy. So you can substitute 
PyQt5 for: PyQt4, PySide2 or PySide. However, for now only compatibility with 
PyQt5 is tested, so naturally it is also recomended.

Versions that are equal to listed vesions are tested. Higher vesions should
work lower may also but are not guaranted to.

Installation
^^^^^^^^^^^^

All modules are found in PyPI so installing should be as easy as:

.. code-block:: bash

    git clone git@github.com:marian-code/wikipedia-music-tags.git
    cd wikipedia-music-tags
    pip install -r requirements.txt

The app CLI and GUI version can be run by:

.. code-block:: bash

    python app_cli.py
    python app_gui.py

**library** submodule can also be used as a library for getting music tags,
lyrics and writing them to files

packages that are not necessary:

* *python-Levenshtein* makes fuzzywuzzy a whole lot faster
* *lxml* makes Beautifulsoup a whole lot faster
* *PyQt5* if you want to use console mode or other Qt backend

If you want to build the frozen app you hate to install aditional libraries.

.. code-block:: bash

    pip install -r setup/requirements.txt

And if you want to build the docs:

.. code-block:: bash

    pip install -r docs/requirements.txt

Since the docs are built automatically on commit to git repo it is not
necessary to build them locally but it is worth checking if there are any
errors beforecommiting to git.



Building frozen app
^^^^^^^^^^^^^^^^^^^

.. warning::
    I **strongly recomend** that you create a virtual environment before
    proceeding, with only requirements needed for this project. Otherwise
    pyinstaller will bundle too many useless libraries in frozen app.
    The frozen app size can easily get over 1GB then. For the same reasons
    Anaconda installation is even worse because it has so many libraries by
    default. If for some strange reason you don't want to create virtual env
    you can use option ``--exclude-module=<module_name>`` in freeze.py to
    exclude unwanted libraries. See section `Creating virtual environment`_

There is one optional optimization which you can do before building frozen app.
You can use 'vanilla' numpy to further reduce size of freezed app. Vanilla
numpy build can be downloaded from here:
`numpy vanilla <https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy>`_.
The problem with regular numpy is building against OPENBLAS (pip version ~40MB)
or Intel MKL (Anaconda version ~ 300MB). Once you've downloaded wheel package
for your python version, install it by:

.. code-block:: bash

    pip install <package-name>.whl

Now you are ready to go:

.. code-block:: bash

    cd setup/

To build the CLI app:

.. code-block:: bash

    python freeze.py cli

When building in virtual env the frozen app should have ~ 75MB.
Without vanilla numpy ~105MB.

To build the GUI app:

.. code-block:: bash

    python freeze.py gui

When building in virtual env the frozen app should have ~ 120MB.
Without vanilla numpy ~150MB.

This will generate list three directories under setup/ folder: gdist/ cdist/
and build/. Build contains just pyinstaller help files and **(g/c)dist/wiki_music**
contain packaged **G**UI and **C**LI console apps. 

Creating virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python, virtual environment can be created and activated by:

.. code-block:: bash

    python3 -m venv /path/to/new/virtual/environment
    source <venv>/bin/activate (Posix)
    <venv>\Scripts\activate.bat (Windows)

For more details see:
`Python env <https://docs.python.org/3/tutorial/venv.html>`_

Anaconda (environment with pip) creation and activation:

.. code-block:: bash

    conda create --prefix /path/to/new/virtual/environment pip
    conda activate /path/to/new/virtual/environment

For more details see:
`Conda env <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ 
