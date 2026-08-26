from __future__ import annotations

import sys
from pathlib import Path

from pyflakes import messages
from pyflakes.api import checkRecursive
from pyflakes.reporter import Reporter


ROOT = Path(__file__).resolve().parents[1]


class UndefinedNameReporter(Reporter):
    def __init__(self):
        super().__init__(sys.stdout, sys.stderr)
        self.failures = 0

    def flake(self, message):
        if isinstance(message, messages.UndefinedName):
            self.failures += 1
            super().flake(message)

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.failures += 1
        super().syntaxError(filename, msg, lineno, offset, text)

    def unexpectedError(self, filename, msg):
        self.failures += 1
        super().unexpectedError(filename, msg)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    paths = args or [
        str(ROOT / 'phase_c2a'),
        str(ROOT / 'scripts'),
        str(ROOT / 'tests'),
    ]
    reporter = UndefinedNameReporter()
    checkRecursive(paths, reporter)
    return 0 if reporter.failures == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
