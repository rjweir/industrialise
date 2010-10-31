# -*- test-case-name: "industrialise.tests.test_browser" -*-

import urllib2
import cookielib

class Browser(object):
    """A pretend browser.  Holds state for a browsing session."""

    def __init__(self):
        self._cookiejar = cookielib.CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))

    def go(self, url):
        """Visit the provided url."""

