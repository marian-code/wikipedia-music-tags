#-----------------------------------------------------------------------------
# Copyright (c) 2005-2019, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------


# hook for nltk
import nltk
from os import path
from PyInstaller.utils.hooks import collect_data_files

# add datas for nltk
datas = collect_data_files('nltk', False)

# loop through the data directories and add them
nltk_source = [p for p in nltk.data.path if path.exists(p)]

# path must be only one
assert len(nltk_source) == 1, "NLTK path must be unique"

nltk_source = nltk_source[0]

nltk_target = "nltk_data"

INCLUDE = [("corpora", "words"),
            ("chunkers", "maxent_ne_chunker"),
            ("taggers", "averaged_perceptron_tagger"),
            ("corpora", "stopwords", "english"),
            ("tokenizers", "punkt", "english.pickle"),
            ("tokenizers", "punkt", "PY3", "english.pickle")]

for i in INCLUDE:
    src = path.join(nltk_source, *i)
    dst = path.join(nltk_target, *i)

    # if source is file than target is only base dir
    if path.isfile(src):
        dst = path.dirname(dst)

    datas.append((src, dst))

# nltk.chunk.named_entity should be included
hiddenimports = ["nltk.chunk.named_entity"]
