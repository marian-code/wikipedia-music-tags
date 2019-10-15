API reference
=============


This file describes wiki_music API reference. Beware, some things might not be
up to date and all is subject to change since we are still in early
development phase.

We often use throughout the documentation notation same as python 
`typing <https://docs.python.org/3/library/typing.html>`_. 
module to mark variable types as it is richer and preserves more information.
e.g. List[str] obviously means list of strings. More on the matter can be
read in the typing module documentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api_gui
   api_library_parser
   api_library_tags
   api_library_lyrics
   api_external_libraries
   api_utilities
   api_constants

wiki_music main
---------------
.. automodule:: wiki_music
   :members:

wiki_music gui
--------------
.. automodule:: wiki_music.app_gui
   :members:

wiki_music cli
--------------
.. automodule:: wiki_music.app_cli
   :members:
