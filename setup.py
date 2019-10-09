import os
from setuptools import setup, find_packages

# The directory containing this file
PKG_ROOT = os.path.dirname(__file__)

# Read package constants
with open(os.path.join(PKG_ROOT, "README.md"), "r") as f:
    README = f.read()

with open(os.path.join(PKG_ROOT, "wiki_music", "version.py"), "r") as f:
    VERSION = f.read().split(" = ")[1]

with open(os.path.join(PKG_ROOT, "requirements.txt"), "r") as f:
    REQUIREMENTS = f.read().split("\n")

# This call to setup() does all the work
setup(
    name="wiki-music",
    version=VERSION,
    description="Music tagger with information retrieval from wikipedia",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/marian-code/wikipedia-music-tags",
    author="Marián Rynik",
    author_email="marian.rynik@outlook.sk",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=("setup", "tests")),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "wiki_music_gui=wiki_music.app_gui:main",
            "wiki_music_cli=wiki_music.app_cli:main",
        ]
    },
)