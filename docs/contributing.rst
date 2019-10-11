Contributing Guide
==================

Running the tests
-----------------

Tests are in early development stage. Make sure all unittests designated by
test\_*.py in tests dir pass. For now we still heavily rely on exploratory
testing.

Coding style tests
------------------

We try to ahere to python recomended coding style quite strictly so we use
these lintners:

* pylint
* pycodestyle(pep8) - style recomendations for python code
* mypy - static typechecking
* pydocstyle - doc style recomendations, this is not followed as strictly
  because we use
  `numpy <https://numpydoc.readthedocs.io/en/latest/format.html>`_ dostrings.

Please follow these style guides as they facilitate an easier shared
developement.

Where to start
--------------

There are some TODOs scattered around the code and created issues so thats a good place to start. 
There is also a list of TODOs maintained in :doc:`Code Changelog <../changelog>`. 
Please log changes to this file.

Changing User interface
-----------------------

Base user interface layout should be changed only with the use of Qt designer and use of files:
``CoverArtEdit.ui``, ``CoverArtSearch.ui``, ``MainWindow.ui``.
The coresponding python files:

Changes to the code before git are in code changelog file.