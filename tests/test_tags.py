import unittest

import os
import sys

# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")))

from wiki_music.constants.tags import TAGS
from wiki_music.library.tags_handler.flac import TagFlac
from wiki_music.library.tags_handler.m4a import TagM4a
from wiki_music.library.tags_handler.mp3 import TagMp3


class TestTagConsistency(unittest.TestCase):

    def test_flac_consistency(self):
        """
        Test that tags in constnts and tag handlers are consistent
        """
        self.assertEqual(sorted(TagFlac.map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_m4a_consistency(self):
        """
        Test that tags in constnts and tag handlers are consistent
        """
        self.assertEqual(sorted(TagM4a.map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_mp3_consistency(self):
        """
        Test that tags in constnts and tag handlers are consistent
        """
        self.assertEqual(sorted(TagMp3.map_keys.values()), sorted(TAGS + ("COMMENT",)))

if __name__ == '__main__':
    unittest.main()