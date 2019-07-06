#!/usr/bin/env python

import asyncio
import json
import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any

import lyricsfinder

_DEFAULT = object()

config_location = Path.home() / ".lyricsfinder"
_config = None


def load_config() -> None:
    global _config

    if not config_location.is_file():
        raise FileNotFoundError("No .lyricsfinder file found in home directory!")

    try:
        data = json.loads(config_location.read_text("utf-8"))
    except json.JSONDecodeError:
        config_location.unlink()
        raise TypeError("Couldn't parse lyricsfinder config...")
    else:
        if not isinstance(data, dict):
            raise TypeError("Wrong data type stored in config file")

        _config = data


def save_config():
    config_location.write_text(json.dumps(_config), "utf-8")


def config_get(key: str, default=_DEFAULT) -> Any:
    if not _config:
        try:
            load_config()
        except FileNotFoundError:
            if default is _DEFAULT:
                raise
            return default

    value = _config.get(key, default)
    if value is _DEFAULT:
        raise KeyError(f"Config doesn't have key {key}")
    return value


def config_set(key: str, value: Any, *, flush=True) -> None:
    global _config

    if not _config:
        try:
            load_config()
        except FileNotFoundError:
            _config = {}

    _config[key] = value
    if flush:
        save_config()


def print_lyrics(lyrics: lyricsfinder.Lyrics) -> None:
    if not lyrics:
        return

    title = lyrics.title or "Unknown"
    artist = lyrics.artist or "Unknown"

    header = f"{title} by {artist}"
    if lyrics.release_date:
        header += f" ({lyrics.release_date.year})"

    width = max(len(header), 40)
    header = header.center(width)
    line = width * "="

    lyrics_text = textwrap.fill(lyrics.lyrics, width, replace_whitespace=False, drop_whitespace=False)

    text = f"{header}\n" \
           f"{line}\n" \
           f"{lyrics_text}\n" \
           f"\n" \
           f"from {lyrics.origin.source_name}"

    print(text)


async def _search_first(query: str, api_key: str) -> lyricsfinder.Lyrics:
    return await lyricsfinder.search_lyrics(query, api_key=api_key)


def search(args: Namespace) -> None:
    api_key = args.token
    if api_key is None:
        api_key = config_get("google_api_key", None)
        if not api_key:
            raise ValueError("No API key specified, and none saved!")
    else:
        config_set("google_api_key", api_key)

    query = " ".join(args.query)
    lyrics = asyncio.run(_search_first(query, api_key=api_key))
    print_lyrics(lyrics)


def extract(args: Namespace) -> None:
    lyrics = asyncio.run(lyricsfinder.extract_lyrics(args.url))
    print_lyrics(lyrics)


def main(*args) -> None:
    args = args or None

    parser = ArgumentParser("lyricsfinder", description="Find the lyrics you've always wanted to find")
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser("search")
    search_parser.set_defaults(func=search)
    search_parser.add_argument("query", help="Query to search for", nargs="+")
    search_parser.add_argument("-t", "--token", help="Google Search API key")

    extract_parser = subparsers.add_parser("extract")
    extract_parser.set_defaults(func=extract)
    extract_parser.add_argument("url", help="Url to extract lyrics from")

    args = parser.parse_args(args)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
