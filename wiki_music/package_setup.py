""" Provides path manipulation magic so we can import from wiki_music in the
package itself.
"""

import os
import sys


def we_are_frozen() -> bool:
    """ Checks if the running code is frozen (e.g by cx-Freeze, pyinstaller).
    
    See also
    --------
    :func:`wiki_music.utilities.utils.we_are_frozen`
        this is a duplicate of the referenced function because it needs to be
        available before the ref. can be imported

    Returns
    -------
    bool
        True if the code is frozen
    """

    # All of the modules are built-in to the interpreter
    return hasattr(sys, "frozen")


def module_path() -> str:
    """ Outputs root path of the module. Acounts for changes in path when
    app is frozen.

    See also
    --------
    :func:`wiki_music.utilities.utils.module_path`
        this is a duplicate of the referenced function because it needs to be
        available before the ref. can be imported
    
    Returns
    -------
    str
        string with root module path

    See also
    --------
    :func:`we_are_frozen`
    """

    if we_are_frozen():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)


# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(module_path(), "..")))

"""
if we_are_frozen():
    f = open(os.devnull, 'w')
    sys.stdout = f
    sys.stderr = f
"""
