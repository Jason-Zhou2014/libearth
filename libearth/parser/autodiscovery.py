""":mod:`libearth.parser.autodiscovery` --- Autodiscovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides functions to autodiscovery feed url in document.

"""
try:
    import HTMLParser
except ImportError:
    import html.parser as HTMLParser
import collections
import re
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from libearth.compat import text
from libearth.parser.heuristic import get_format
from libearth.parser import atom, rss2


__all__ = 'autodiscovery',


#: (:class:`str`) The MIME type of RSS 2.0 format.
RSS_TYPE = 'application/rss+xml'

#: (:class:`str`) The MIME type of Atom format.
ATOM_TYPE = 'application/atom+xml'


link_tuple = collections.namedtuple('link_tuple', 'type url')


def autodiscovery(document, url):
    """If the given url refers an actual feed, it returns the given url
    without any change.

    If the given url is a url of an ordinary web page
    (i.e. :mimetype:`text/html`), it finds the urls of the corresponding feed.
    It sorts feed urls in lexicographical order of feed types and return urls.

    If autodiscovery failed, it raise :exc:`FeedUrlNotFoundError`.

    :param document: html, or xml strings
    :type document: :class:`str`
    :param url: the url used to retrieve the ``document``.
                if feed url is in html and represented in relative url,
                it will be rebuilt on top of the ``url``
    :type url: :class:`str`
    :returns: list of `namedtuple('link_tuple', 'type url')`
    :rtype: :class:`collections.MutableSequence`

    """
    document = text(document)
    document_type = get_format(document)
    if document_type is None:
        parser = AutoDiscovery()
        feed_links = parser.find_feed_url(document)
        if not feed_links:
            raise FeedUrlNotFoundError('Cannot find feed url')
        for link in feed_links:
            if link.url.startswith('/'):
                absolute_url = urlparse.urljoin(url, link.url)
                feed_links.insert(feed_links.index(link),
                                  link_tuple(link.type, absolute_url))
                feed_links.remove(link)
        return feed_links
    else:
        if document_type == atom.parse_atom:
            return [link_tuple(ATOM_TYPE, url)]
        elif document_type == rss2.parse_rss:
            return [link_tuple(RSS_TYPE, url)]


class AutoDiscovery(HTMLParser.HTMLParser):
    """Parse the given HTML and try finding the actual feed urls from it."""

    def __init__(self):
        self.feed_links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and 'rel' in attrs and attrs['rel'] == 'alternate' \
                and 'type' in attrs and attrs['type'] in RSS_TYPE+ATOM_TYPE:
            self.feed_links.append(link_tuple(attrs['type'], attrs['href']))

    def find_feed_url(self, document):
        match = re.match('.+</head>', document)
        if match:
            head = match.group(0)
        else:
            head = document
        chunks = re.findall('[^>]*(?:>|$)', head)
        for chunk in chunks:
            try:
                self.feed(chunk)
            except:
                self.find_feed_url_with_regex(chunk)
        self.feed_links = sorted(self.feed_links, key=lambda link: link.type)
        return self.feed_links

    def find_feed_url_with_regex(self, chunk):
        if (re.search('rel\s?=\s?(\'|")?alternate[\'"\s>]', chunk) and
                (RSS_TYPE in chunk) or (ATOM_TYPE in chunk)):
            feed_url = re.search('href\s?=\s?(?:\'|")?([^\'"\s>]+)',
                                 chunk).group(1)
            feed_type = re.search('type\s?=\s?(?:\'|\")?([^\'"\s>]+)',
                                  chunk).group(1)
            self.feed_links.append(link_tuple(feed_type, feed_url))


class FeedUrlNotFoundError(Exception):
    """Exception raised when feed url cannot be found in html."""

    def __init__(self, msg):
        self.msg = msg
