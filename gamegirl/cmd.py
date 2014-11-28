#!/usr/bin/env python
"""
Execute a GameBoy ROM.

Usage: gamegirl FILENAME

Options:
  --help                  Show this screen.
  --version               Show version.
"""
from docopt import docopt

import gamegirl


def main():
    args = docopt(__doc__, version=gamegirl.__version__)
    print args['FILENAME']


if __name__ == 'main':
    main()
