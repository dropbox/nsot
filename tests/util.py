"""
General purpose utilities for unit-testing.
"""

import json
import os


__all__ = ('load_json',)


def load_json(relpath):
    """
    Load JSON files relative to ``tests`` directory.

    Files are loaded from the 'data' directory. So for example for
    ``/path/to/data/devices/foo.json`` the ``relpath`` would be
    ``data/devices/foo.json``.

    :param relpath:
        Relative path to our directory's "data" dir
    """
    our_path = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(our_path, relpath)
    with open(filepath, 'rb') as f:
        return json.load(f)
