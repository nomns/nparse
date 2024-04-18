# Nomns' Parser for Project1999


Provides player location and spell tracking support for Project 1999 by reading the player log.

Now with location sharing, path recording, and Discord overlay!

Please see the [Wiki](https://github.com/nomns/nparse/wiki) for more information or go to the [Releases](https://github.com/nomns/nparse/releases) for the latest release.

Building
========

Install Python 3.12.x and install requirements with `pip install -r requirements.txt`

Note: Currently it seems problematic to build PyQt6 on 32-bit Python.

Install `pyinstaller==6.6.0`

Run: `pyinstaller nparse_py.spec`