import unittest

import setup_tests
from wiki_music.constants.tags import TAGS
from wiki_music.library.tags_handler.flac import TagFlac
from wiki_music.library.tags_handler.m4a import TagM4a
from wiki_music.library.tags_handler.mp3 import TagMp3


class TestTagConsistency(unittest.TestCase):
    """ Test that tags in constnts and tag handlers are consistent """

    def test_flac_consistency(self):
        self.assertEqual(sorted(TagFlac.map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_m4a_consistency(self):
        self.assertEqual(sorted(TagM4a.map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_mp3_consistency(self):
        self.assertEqual(sorted(TagMp3.map_keys.values()), sorted(TAGS + ("COMMENT",)))

if __name__ == '__main__':
    unittest.main()
