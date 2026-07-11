#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from importlib import reload

from cli_profile_manager import cli as _cli

if getattr(_cli, "_PROFILE_MANAGER_COMPAT_LOADED", False):
    reload(_cli)
_cli._PROFILE_MANAGER_COMPAT_LOADED = True
from cli_profile_manager.cli import *  # noqa: E402,F401,F403 - compatibility surface
from cli_profile_manager.cli import main  # noqa: E402


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        from cli_profile_manager.interactive import clear_screen

        clear_screen()
        sys.exit(0)
