"""Test documentation build."""

import unittest
import subprocess
import logging
from pathlib import Path

from . import setup_tests

DOCS_ROOT = str((Path(__file__).parent / ".." / "docs").resolve())

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TestDocsBuild(unittest.TestCase):
    """Check for docs build warnings."""

    def setUp(self):

        try:
            output = subprocess.run(["make", "html"], capture_output=True,
                                    check=True, shell=True, universal_newlines=True,
                                    cwd=DOCS_ROOT)
        except subprocess.CalledProcessError:
            log.exception(DOCS_ROOT)
            self.stdout = None
            self.stderr = None
        else:
            self.stdout = output.stdout
            self.stderr = output.stderr

    def test_build_gave_output(self):
        self.assertNotEqual(self.stdout, None)

    def test_build_crashed(self):

        if "RemovedInSphinx30Warning" in self.stderr:
            stderr = None
        else:
            stderr = self.stderr

        self.assertFalse(stderr)

    def test_build_no_warnings(self):

        if "WARNING" in self.stdout:
            has_warning = True
        else:
            has_warning = False

        self.assertFalse(has_warning)

    def test_build_no_exceptions(self):

        for e in ("EXCEPTION", "ERROR", "CRITICAL"):
            if e in self.stdout:
                has_warning = True
                break
        else:
            has_warning = False

        self.assertFalse(has_warning)

    def test_build_successful(self):

        self.assertIn("build succeeded.", self.stdout)


if __name__ == '__main__':
    unittest.main()
