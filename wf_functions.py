#This is sort of a lift of the web2py book to make at least somewhat compatible with py4web and
#get most of my markmin files surfaced as html on py4web

from pydal._compat import to_native, to_bytes, to_unicode
from pydal.validators import *


def splitter(x):
    a, b = x.split(':', 1)
    return a.strip(), b.strip()

def splitter_urlify(x):
    x = to_native(x)
    a, b = x.split(':', 1)
    return a.strip(), b.strip(), IS_SLUG()(b)[0]
