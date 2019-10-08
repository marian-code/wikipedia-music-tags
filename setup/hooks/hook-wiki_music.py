hiddenimports =[
    "wiki_music.version",
    "wiki_music.package_setup",
    # all the following are lazy loaded so pyinstaller cannot find them
    "wiki_music.library.tags_handler.tag_base",
    "wiki_music.library.tags_handler.mp3",
    "wiki_music.library.tags_handler.m4a",
    "wiki_music.library.tags_handler.flac",
    "wiki_music.external_libraries.lyricsfinder.extractors.animelyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.azlyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.darklyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.genius",
    "wiki_music.external_libraries.lyricsfinder.extractors.lyrical_nonsense",
    "wiki_music.external_libraries.lyricsfinder.extractors.lyricsmode",
    "wiki_music.external_libraries.lyricsfinder.extractors.musixmatch",
]