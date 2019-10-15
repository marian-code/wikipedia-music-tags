Usage instructions
==================

As an application
-----------------

If you have installed wiki_music with setup.py install or from PyPi you can
use two scripts provided by the package:

.. code-block:: bash

    wiki_music_cli(.exe)

which runs the CLI app, and

.. code-block:: bash

    wiki_music_gui(.exe)

which runs the GUI app. Both can be run with -h or --help to list addinional
command line parameters.

As a library
------------

You can also incorporate wiki_music capabilities into you own code, by
importing it and using its modules.

A simple example would be to run the GUI or CLI app:

.. code-block:: python

    >>> import wiki_music
    >>> wiki_music.app_cli.main()
    >>> wiki_music.app_gui.main()

You can also call the library methods and classes directly for example to
save lyrics:

.. code-block:: python

    >>> from import wiki_music.library.lyrics import save_lyrics
    >>> save_lyrics(<tracks list>, <track types list>, <band>, <album>,
                    GUI=False)
        <list of lyrics>

or for user friendly tag writing to file:

.. code-block:: python

    >>> from import wiki_music.library.tags_io import (write_tags, read_tags,
                                                       supported_tags)
    >>> supported_tags()
    wiki_music supports these tags:
    ALBUM, ALBUMARTIST, ARTIST, COMPOSER, COVERART, DATE, DISCNUMBER, GENRE,
    LYRICS, TITLE, TRACKNUMBER
    >>> read_tags(<some_path/Firelights.m4a>)
    {'ALBUM': 'When A Shadow Is Forced Into The Light',
     'ALBUMARTIST': 'Swallow The Sun',
     'ARTIST': ['Swallow The Sun'],
     'COMMENT': '',
     'COMPOSER': ['Juha Raivio'],
     'DATE': '2019',
     'DISCNUMBER': '1',
     'GENRE': 'Doom metal',
     'LYRICS': "[Verse 1]\r\nI'm drowning\r\nIn t..
                ..ow\r\nInside the fires burning bright",
     'TITLE': 'Firelights',
     'TRACKNUMBER': '3',
     'COVERART': MP4Cover(b'\xff\xd8\xff\xe0\x0.....ff\xd9',
                          <AtomDataType.JPEG: 13>)}
    >>> write_tags(<tags dict>)

You can initialize the parser and call its methods:

.. code-block:: python

    >>> from wiki_music.library.parser.process_page import WikipediaParser
    >>> parser = WikipediaParser()
    >>> parser.ALBUM = "When A Shadow Is Forced Into The Light"
    >>> parser.ALBUMARTIST = "Swallow The Sun"
    >>> parser.get_wiki()
    >>> parser.url
    'https://en.wikipedia.org/wiki/When_a_Shadow_Is_Forced_into_the_Light'
    >>> parser.cook_soup()
    >>> parser.get_contents()
    >>> parser.contents
    ['Track listing', 'Personnel', 'Charts', 'References']
    >>> parser.get_contents()
    >>> parser.contents
    ['Track listing', 'Personnel', 'Charts', 'References']
    >>> parser.get_genres()
    >>> parser.genres
    ['Post-metal', 'gothic metal', 'black metal', 'doom metal']
    >>> parser.get_personnel()
    >>> parser.personnel
    ['Mikko Kotamäki',  'Juho Räihä', 'Juha Raivio', 'Jaani Peuhu',
     'Matti Honkonen', 'Juuso Raatikainen']

and so on ... For more details see API reference.