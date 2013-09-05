""":mod:`libearth.feed` --- Feeds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:mod:`libearth` internally stores archive data as Atom format.  It's exactly
not a complete set of :rfc:`4287`, but a subset of the most of that.
Since it's not intended for crawling but internal representation, it does not
follow robustness principle or such thing.  It simply treats stored data are
all valid and well-formed.

"""
import cgi
try:
    import HTMLParser
except ImportError:
    from html import parser as HTMLParser

from .codecs import Enum
from .compat import UNICODE_BY_DEFAULT, text_type
from .schema import Attribute, Content, Element, Text as TextChild

__all__ = 'ATOM_XMLNS', 'MarkupTagCleaner', 'Person', 'Text'


#: (:class:`str`) The XML namespace name used for Atom (:rfc:`4287`).
ATOM_XMLNS = 'http://www.w3.org/2005/Atom'


class MarkupTagCleaner(HTMLParser.HTMLParser):
    """Strip all markup tags from HTML string."""

    @classmethod
    def clean(cls, html):
        parser = cls()
        parser.feed(html)
        return ''.join(parser.fed)

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)


class Text(Element):
    """Text construct defined in :rfc:`4287#section-3.1` (section 3.1)."""

    #: (:class:`str`) The type of the text.  It could be one of ``'text'``
    #: or ``'html'``.  It corresponds to :rfc:`4287#section-3.1.1` (section
    #: 3.1.1).
    #:
    #: .. note::
    #:
    #:    It currently does not support ``'xhtml'``.
    #:
    #: .. todo::
    #:
    #:    Default value should be ``'text'``.
    type = Attribute('type', Enum(['text', 'html']), required=True)

    #: (:class:`str`) The content of the text.  Interpretation for this
    #: has to differ according to its :attr:`type`.  It corresponds to
    #: :rfc:`4287#section-3.1.1.1` (section 3.1.1.1) if :attr:`type` is
    #: ``'text'``, and :rfc:`4287#section-3.1.1.2` (section 3.1.1.2) if
    #: :attr:`type` is ``'html'``.
    value = Content()

    def __unicode__(self):
        if self.type == 'html':
            return MarkupTagCleaner.clean(self.value)
        elif self.type == 'text':
            return self.value

    if UNICODE_BY_DEFAULT:
        __str__ = __unicode__
    else:
        __str__ = lambda self: unicode(self).encode('utf-8')

    def __html__(self):
        if self.type == 'html':
            return self.value
        elif self.type == 'text':
            return cgi.escape(self.value, quote=True).replace('\n', '<br>\n')

    def __repr__(self):
        return '{0.__module__}.{0.__name__}(type={1!r}, value={2!r})'.format(
            type(self), self.type, self.value
        )


class Person(Element):
    """Person construct defined in :rfc:`4287#section-3.2` (section 3.2)."""

    #: (:class:`str`) The human-readable name for the person.  It corresponds
    #: to ``atom:name`` element of :rfc:`4287#section-3.2.1` (section 3.2.1).
    name = TextChild('name', xmlns=ATOM_XMLNS, required=True)

    #: (:class:`str`) The optional URI associated with the person.
    #: It corresponds to ``atom:uri`` element of :rfc:`4287#section-3.2.2`
    #: (section 3.2.2).
    uri = TextChild('uri', xmlns=ATOM_XMLNS)

    #: (:class:`str`) The optional email address associated with the person.
    #: It corresponds to ``atom:email`` element of :rfc:`4287#section-3.2.3`
    #: (section 3.2.3).
    email = TextChild('email', xmlns=ATOM_XMLNS)

    def __unicode__(self):
        ref = self.uri or self.email
        if ref:
            return text_type('{0} <{1}>').format(self.name, ref)
        return self.name

    if UNICODE_BY_DEFAULT:
        __str__ = __unicode__
    else:
        __str__ = lambda self: unicode(self).encode('utf-8')

    def __html__(self):
        name = cgi.escape(self.name, quote=True)
        ref = self.uri or self.email and 'mailto:' + self.email
        if ref:
            return text_type('<a href="{1}">{0}</a>').format(
                name,
                cgi.escape(ref, quote=True)
            )
        return name

    def __repr__(self):
        return ('{0.__module__}.{0.__name__}(name={1!r}, uri={2!r}'
                ', email={3!r})').format(type(self), self.name, self.uri,
                                         self.email)