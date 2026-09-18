from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# <version of Qwen Code, at least X.Y.Z>.<app version>
VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+){3,}$")


def read_package_version() -> str:
    source = (PROJECT_ROOT / "src" / "qwencode_branch_stats" / "__init__.py").read_text(
        encoding="utf-8"
    )
    match = re.search(r'^__version__ = "([^"]+)"$', source, re.MULTILINE)
    if match is None:
        raise AssertionError("__version__ not found in package __init__.py")
    return match.group(1)


def read_pyproject_version() -> str:
    source = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', source, re.MULTILINE)
    if match is None:
        raise AssertionError("version not found in pyproject.toml [project]")
    return match.group(1)


class VersionFormatTest(unittest.TestCase):
    def test_version_follows_qwen_plus_app_format(self):
        self.assertRegex(read_package_version(), VERSION_PATTERN)

    def test_pyproject_and_package_versions_match(self):
        self.assertEqual(read_pyproject_version(), read_package_version())


if __name__ == "__main__":
    unittest.main()
