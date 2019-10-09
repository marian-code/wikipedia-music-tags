""" Manipulate path so tests can import wiki_music_package. """
import os
import sys

# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__),
                                              "..")))
