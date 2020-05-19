"""Test documentation build."""

import unittest
from subprocess import run, CalledProcessError, PIPE
import logging
from pathlib import Path

DOCS_ROOT = str((Path(__file__).parent.parent / "docs").resolve())

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TestDocsBuild(unittest.TestCase):
    """Check for docs build warnings."""

    def setUp(self):

        try:
            # use PIPEs instead of capture output because it is supported only
            # in py3.7 and higher
            output = run("make html", stdout=PIPE, stderr=PIPE,
                         check=True, shell=True, universal_newlines=True,
                         cwd=DOCS_ROOT)
        except CalledProcessError:
            log.exception(DOCS_ROOT)
            self.stdout = None
            self.stderr = None
        else:
            self.stdout = output.stdout
            self.stderr = output.stderr

    def test_bld(self):

        output = run("make html", stdout=PIPE, stderr=PIPE,
                     check=False, shell=True, universal_newlines=True,
                     cwd=DOCS_ROOT)

        log.exception(output)
        log.exception(output.stdout)
        log.exception(output.stderr)

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
        log.debug(self.stdout)

        self.assertIn("build succeeded", self.stdout)


if __name__ == '__main__':
    unittest.main()
