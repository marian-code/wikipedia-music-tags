import os
import sys

# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")))

from wiki_music.library.tags_handler import File
from wiki_music.library.tags_io import read_tags, write_tags
from pprint import pprint
from PIL import Image
from io import BytesIO
from time import sleep


def test_cover_art(path):

    with open("input.jpg", "rb") as f:
        bytes_image = f.read()

    song = File(path)
    song.tags["COVERART"] = bytes_image
    song.save()

    song = File(path)
    bytes_image_new = song.tags["COVERART"][0]

    if bytes_image == bytes_image_new:
        return True
    else:
        return False


def test_high_level_write_read(path):

    data = dict(read_tags(path))
    data["FILE"] = path
    data["TYPE"] = ""
    print("------------------------------------")
    print_tags(data)

    write_tags(data, False)

    new_data = dict(read_tags(path))
    new_data["FILE"] = path
    new_data["TYPE"] = ""

    if data == new_data:
        return True
    else:
        return False


def print_tags(tags_dict):

    for k, v in tags_dict.items():
        if "LYRICS" in k:
            print(f"{k:11}: {v[:30]} ...")
        elif k != "COVERART":
            print(f"{k:11}: {v}")
        elif k == "COVERART":
            im = Image.open(BytesIO(v))
            im.show()


work_dir = os.getcwd()

files = ["Aventine.mp3", "Aventine.flac", "Aventine.m4a"]
files = [os.path.join(work_dir, "test_music", f) for f in files]

"""
for f in files:
    print(f"Testing {os.path.basename(f):15}: ", end="")
    result = test_cover_art(f)
    if result:
        print("success")
    else:
        print("fail")
"""


for f in files:
    print(f"Testing {os.path.basename(f):15}: ", end="")
    result = test_high_level_write_read(f)
    if result:
        print("success")
    else:
        print("fail")
