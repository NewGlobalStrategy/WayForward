#This is sort of a lift of the web2py book to make at least somewhat compatible with py4web and
#get most of my markmin files surfaced as html on py4web

from pydal._compat import to_native, to_bytes, to_unicode
from pydal.validators import *
from markmin import markmin2html
from py4web import URL
from yatl.helpers import DIV, XML, CAT


def splitter(x):
    a, b = x.split(':', 1)
    return a.strip(), b.strip()

def splitter_urlify(x):
    x = to_native(x)
    a, b = x.split(':', 1)
    return a.strip(), b.strip(), IS_SLUG()(b)[0]


class XmlComponent(object):
    """
    Abstract root for all Html components
    """

    # TODO: move some DIV methods to here

    def xml(self):
        raise NotImplementedError

    def __mul__(self, n):
        return CAT(*[self for i in range(n)])

    def __add__(self, other):
        if isinstance(self, CAT):
            components = self.components
        else:
            components = [self]
        if isinstance(other, CAT):
            components += other.components
        else:
            components += [other]
        return CAT(*components)

    def add_class(self, name):
        """
        add a class to _class attribute
        """
        c = self['_class']
        classes = (set(c.split()) if c else set()) | set(name.split())
        self['_class'] = ' '.join(classes) if classes else None
        return self

    def remove_class(self, name):
        """
        remove a class from _class attribute
        """
        c = self['_class']
        classes = (set(c.split()) if c else set()) - set(name.split())
        self['_class'] = ' '.join(classes) if classes else None
        return self


# Below lifted from web2py gluon.html as not part of YATL.Helpers
class MARKMIN(XmlComponent):
    """
    For documentation: http://web2py.com/examples/static/markmin.html
    """
    def __init__(self,
                 text, extra=None, allowed=None, sep='p',
                 url=None, environment=None, latex='google',
                 autolinks='default',
                 protolinks='default',
                 class_prefix='',
                 id_prefix='markmin_',
                 **kwargs):
        self.text = to_bytes(text)
        self.extra = extra or {}
        self.allowed = allowed or {}
        self.sep = sep
        self.url = URL if url is True else url
        self.environment = environment
        self.latex = latex
        self.autolinks = autolinks
        self.protolinks = protolinks
        self.class_prefix = class_prefix
        self.id_prefix = id_prefix
        self.kwargs = kwargs

    def flatten(self):
        return self.text

    def xml(self):
        from markmin.markmin2html import render
        html = render(self.text, extra=self.extra,
                      allowed=self.allowed, sep=self.sep, latex=self.latex,
                      URL=self.url, environment=self.environment,
                      autolinks=self.autolinks, protolinks=self.protolinks,
                      class_prefix=self.class_prefix, id_prefix=self.id_prefix)
        return to_bytes(html) if not self.kwargs else to_bytes(DIV(XML(html), **self.kwargs).xml())

    def __str__(self):
        # In PY3 __str__ cannot return bytes (TypeError: __str__ returned non-string (type bytes))
        return to_native(self.xml())
