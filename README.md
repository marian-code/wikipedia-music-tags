# Wikipegia music tags parser

![PyPI](https://img.shields.io/pypi/v/wiki-music)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wiki-music)
[![license](https://img.shields.io/pypi/l/qtpy.svg)](./LICENSE)

[![Documentation Status](https://readthedocs.org/projects/wikipedia-music-tags/badge/?version=latest)](https://wikipedia-music-tags.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/marian-code/wikipedia-music-tags/badge.svg?branch=master)](https://coveralls.io/github/marian-code/wikipedia-music-tags?branch=master)
[![Requirements Status](https://requires.io/github/marian-code/wikipedia-music-tags/requirements.svg?branch=master)](https://requires.io/github/marian-code/wikipedia-music-tags/requirements/?branch=master)
[![Build Status](https://travis-ci.com/marian-code/wikipedia-music-tags.svg?branch=master)](https://travis-ci.com/marian-code/wikipedia-music-tags)



Python application which parses wikipedia for music tags and writes them to 
files. Has also the ability to search for lyrics and album cover art. The app
was created to complement tagging tools that use other datatabases.
I often found that these databases provide only some basic information. For
instance there are no lyrics or composers information, or the cover art is in
low resolution. The Wikipedia is often the most complete source of information
but extracting the information by hand is a slow and boring process.

wiki_music aims to automate this, paired with a powerful image and lyrics
search, tagging often takes only a few clicks. It is not perfect however.
Wikipedia data is not saved in standardized form so it has to be extracted from
html which can at times be unreliable. But the app should always give you at
least some good starting point from which you can continuee editing by hand.

## Getting Started

Package can be installed with pip:

```
pip install wiki_music
```
For more details refer to Documentation which can be found at:
[readthedocs](https://wikipedia-music-tags.readthedocs.io/en/latest/index.html).

[Installation intructions](https://wikipedia-music-tags.readthedocs.io/en/latest/instalation.html)

[Usage intructions](https://wikipedia-music-tags.readthedocs.io/en/latest/usage.html)

[Contributing guide](https://wikipedia-music-tags.readthedocs.io/en/latest/contributing.html)


Anyone is welcome to use it or contribute. All of the dependencies are fairly
common so you shouldn't encounter any problems. Curentlly supported versions of
python are **3.6** - **3.8**.

## Bugs & Features

If there are some features missing or you found a bug please create an issue
at: [Git Issues](https://github.com/marian-code/wikipedia-music-tags/issues)

### Prerequisites

```
appdirs>=1.4.3
beautifulsoup4>=4.6.0
colorama>=0.4.0
datefinder>=0.6.1
fuzzywuzzy>=0.17.0
lazy-import>=0.2.2
lxml>=4.2.1
nltk>=3.3
mutagen>=1.42.0
numpy>=1.14.3
Pillow>=6.1.0
PyQt5>=5.11.3
python-Levenshtein>=0.12.0
QtPy>=1.7.0
requests>=2.18.4
wikipedia>=1.4.0
```

## Authors

* **Marián Rynik** - *Initial work* - [marian-code](https://github.com/marian-code)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

[MIT](https://github.com/marian-code/https://github.com/marian-code/wikipedia-music-tags/LICENSE.txt)

## Acknowledgments

* Stackoverflow
* [Giesela Inc.](https://github.com/GieselaDev) - LyricsFinder
* [https://github.com/hardikvasa](https://github.com/hardikvasa) - google_images_download
* [https://github.com/ppinard/qtango](https://github.com/ppinard/qtango) - Tango icon theme, with qrc generator

