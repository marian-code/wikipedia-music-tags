import unittest

from wiki_music.constants.tags import TAGS, EXTENDED_TAGS
from wiki_music.library.tags_handler.flac import TagFlac
from wiki_music.library.tags_handler.m4a import TagM4a
from wiki_music.library.tags_handler.mp3 import TagMp3
from wiki_music.library.parser.base import ParserBase


class TestTagConsistency(unittest.TestCase):
    """Test that tags in constnts and tag handlers are consistent."""

    def test_flac_consistency(self):
        self.assertEqual(sorted(TagFlac._map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_m4a_consistency(self):
        self.assertEqual(sorted(TagM4a._map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_mp3_consistency(self):
        self.assertEqual(sorted(TagMp3._map_keys.values()), sorted(TAGS + ("COMMENT",)))

    def test_parser_consistency(self):

        for tag in EXTENDED_TAGS:
            with self.subTest(tag=tag):
                self.assertTrue(getattr(ParserBase, tag, None))


if __name__ == '__main__':
    unittest.main()
