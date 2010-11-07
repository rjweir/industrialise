# -*- test-case-name: "industrialise.tests.test_browser" -*-

import urllib2
import cookielib

from lxml.html import fromstring

class Browser(object):
    """A pretend browser.  Holds state for a browsing session."""

    def __init__(self):
        self._cookiejar = cookielib.CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))
        self._cur_url = None
        self._cur_page = None
        self._history = []

    def _load_data(self, url):
        return self._opener.open(url).read()

    def go(self, url):
        """Visit the provided url."""
        self._visit(url)
        self._history.append(url)

    def _visit(self, url):
        self._cur_url = url
        self._cur_page = self._load_data(url)
        self._tree = fromstring(self._cur_page)

    def back(self):
        self._history.pop()
        self._visit(self._history[-1])

    def find(self, path):
        return self._tree.xpath(path)
