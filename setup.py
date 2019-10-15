"""Setup file for wiki_music."""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

# The directory containing this file
PKG_ROOT = os.path.dirname(__file__)

# Read package constants
with open(os.path.join(PKG_ROOT, "README.md"), "r") as f:
    README = f.read()

with open(os.path.join(PKG_ROOT, "wiki_music", "version.py"), "r") as f:
    VERSION = f.read().split(" = ")[1].replace("\"", "")

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
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Environment :: X11 Applications :: Qt",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Typing :: Typed"
    ],
    packages=find_packages(exclude=("setup", "tests")),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "wiki_music_gui=wiki_music.app_gui:main",
            "wiki_music_cli=wiki_music.app_cli:main",
        ]
    },
)

# optional installation of NLTK data
print("\nThe package requires downloading of NLTK data to function to its\n"
      "full potential. It will work without the data, but the extraction\n"
      "will not be as effective. Final size is ~32MB.\n")

# decide if NLTK data should be downloaded
while True:
    inpt = str(input("Do you want to proceed? [y]/n: ")).strip().casefold()

    if not inpt or inpt == "y":
        answer = True
        break
    elif inpt == "n":
        answer = False
        break
    else:
        print("You must input 'y' or 'n'")

# if yes
if answer:

    # get platform specific default path
    # get platform specific default path
    if sys.platform == "win32":
        NLTK_DEFAULT = Path("C:/nltk_data")
    elif sys.platform == "linux":
        NLTK_DEFAULT = Path("/usr/share/nltk_data")
    elif sys.platform == "darwin":
        NLTK_DEFAULT = Path("/usr/local/share/nltk_data")
    else:
        raise Warning("Usupported platform! you must specify path manually.")

    # ask user to specify their own path
    print(
        "\nPlease specify NLTK data installation path or accept the default:\n"
        " - if the path does not exist it will be created\n"
        " - if you specify other than default you wil have to modify your \n"
        "   otherwise nltk will not be able to find data folder\n")
    while True:
        inpt = str(input(f"({NLTK_DEFAULT}[ENTER]): ")).strip()

        if not inpt:
            break
        else:
            NLTK_USER = Path(inpt)

        # check for path being correct
        try:
            os.makedirs(NLTK_USER, exist_ok=True)
        except Exception:
            print("Path is not valid or cannot be created!")
        else:
            NLTK_DEFAULT = NLTK_USER
            print(f"\nAdd this entry to your system PATH variable: "
                  f"NLTK_DATA: {NLTK_DEFAULT}")
            break

    # import NLTK and download data
    import nltk

    print("\nDownloading NLTK data...\n"
          "Download size is ~90MB, Final disk size ~32MB\n")

    nltk.download("words", NLTK_DEFAULT)
    nltk.download("stopwords", NLTK_DEFAULT)
    nltk.download("maxent_ne_chunker", NLTK_DEFAULT)
    nltk.download("averaged_perceptron_tagger", NLTK_DEFAULT)
    nltk.download("punkt", NLTK_DEFAULT)

    # clean unecessary files
    print("\nDeleting unnecessary files...")
    for root, _, files in os.walk(NLTK_DEFAULT):
        for fl in files:
            if fl.endswith((".zip", ".pickle", "README")):
                # avoid deletinng some files
                if "english" not in fl and "_perceptron_tagger.p" not in fl:
                    os.remove(os.path.join(root, fl))

    # set nltk data path
    nltk.data.path.append(NLTK_DEFAULT)

    print("Done.")
