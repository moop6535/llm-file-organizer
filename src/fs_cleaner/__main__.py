"""Entry point for python -m fs_cleaner."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
