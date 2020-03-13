"""Generate icon resource files."""

from pathlib import Path
import shutil
import os
import re
import argparse
import xml.etree.ElementTree as etree
import xml.dom.minidom as minidom
import subprocess

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def create_qrc(themefilepath: str, exts: list = ['.png', '.svg']) -> Path:
    """Generate .qrc file from all images in the directory of the theme path.

    Parameters
    ----------
    themefilepath: str
        path to themefile *.theme
    exts: list
        list of allowed image extensions

    Returns
    -------
    Path
        path to generated *.qrc file
    """
    basepath = Path(themefilepath).parent

    # Parse index.theme
    parser = configparser.ConfigParser()
    parser.read(themefilepath)
    name = parser.get('Icon Theme', 'Name')
    directories = parser.get('Icon Theme', 'Directories').split(',')

    # Create root
    root = etree.Element('RCC', version='1.0')
    element_qresource = etree.SubElement(root, 'qresource',
                                         prefix='icons/%s' % name)

    element = etree.SubElement(element_qresource, 'file', alias='index.theme')
    element.text = str(Path(themefilepath).relative_to(basepath.parent))
    # ! for reference, this is the original implementation
    # element.text = str(Path(themefilepath).resolve())

    # Find all image files
    for directory in directories:
        for filename in (basepath / directory).rglob("*"):
            if filename.is_file() and filename.suffix in exts:
                alias = f"{filename.parent.parent.stem}/{filename.stem}"
                text = str(filename.relative_to(basepath.parent))
                element = etree.SubElement(element_qresource, 'file', alias=alias)
                element.text = text

    # get rid of the stupid header, rcc compilers don't work with it
    doc = minidom.parseString(etree.tostring(root)).toprettyxml()
    doc = "\n".join(doc.splitlines()[1:])

    # Write
    outfilepath = basepath.parent / f"{name}.qrc"
    outfilepath.write_text(doc)

    return outfilepath


def run_rcc(qrcfilepath: Path):
    """Run resource compiler, transform *.qrc --> *.py.

    Parameters
    ----------
    qrcfilepath: str
        path to *.qrc file
    """
    # different possible resource compilers in order of importance
    rccs = ["pyside2-rcc", "pyrcc5", "pyrcc4", "pyside-rcc"]

    # add exe suffixes if we are on windows
    if os.name == "nt":
        for i, r in enumerate(rccs):
            rccs[i] = f"{r}.exe"

    for r in rccs:
        pyrcc = shutil.which(r)
        if pyrcc:
            if os.path.isfile(pyrcc):
                pyrcc = r
                break
    else:
        raise Exception("No python Qt resource compiler was found")

    outfilepath = qrcfilepath.with_suffix(".py")

    out = subprocess.check_output([pyrcc, qrcfilepath.name, "-o",
                                   outfilepath.name],
                                  cwd=outfilepath.parent)


def run():
    """Generates *.qpc and *.py files from available icons."""
    parser = argparse.ArgumentParser(description='Generate rcc')
    parser.add_argument('theme', metavar='FILE', help='Path to .theme file')

    args = parser.parse_args()

    qrcfilepath = create_qrc(args.theme)
    run_rcc(qrcfilepath)


if __name__ == '__main__':
    run()
