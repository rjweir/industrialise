# -*- test-case-name: "industrialise.tests.test_browser" -*-

import urllib
import urllib2
import cookielib

from lxml.html import fromstring, submit_form
import wsgi_intercept
from wsgi_intercept.urllib2_intercept.wsgi_urllib2 import WSGI_HTTPHandler

from industrialise._version import VERSION

class Browser(object):
    """A pretend browser.  Holds state for a browsing session."""

    def __init__(self, cookiejar=None):
        if cookiejar is None:
            cookiejar = cookielib.CookieJar()
        self._cookiejar = cookiejar
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))
        self._tweak_user_agent(self._opener)
        self.url = None
        self.contents = None
        self.history = []

    def _tweak_user_agent(self, opener):
        headers = dict(opener.addheaders)
        headers['User-agent'] = "%s; (Industrialise %s)" % (headers['User-agent'],
                                                           VERSION)
        opener.addheaders = headers.items()

    def _load_data(self, url):
        response = self._opener.open(url)
        self.response_code = response.getcode()
        return response.read(), response.geturl()

    def reload(self):
        self._visit(self.url)

    def go(self, url):
        """Visit the provided url."""
        self._visit(url)
        self.history.append(url)

    def _visit(self, url):
        try:
            self.contents, self.url = self._load_data(url)
            self._tree = fromstring(self.contents, base_url=self.url)
            self.code = 200
        except urllib2.URLError, e:
            self.code = e.code
            self.contents = ''

    def back(self):
        self.history.pop()
        self._visit(self.history[-1])

    def follow(self, content):
        self._tree.make_links_absolute(self.url, resolve_base_href=True)
        links = self._tree.xpath('//a[text() = $content]', content=content)
        if len(links) < 1:
            raise ValueError("Link matching that text not found.")
        elif len(links) > 1:
            raise ValueError("More than one matching link found.")
        self.go(links[0].attrib['href'])

    def find(self, path):
        return self._tree.xpath(path)

    def _open_http(self, method, url, values={}):
        if method == "POST":
            return self._opener.open(url, urllib.urlencode(values))

    def submit(self, form, **kwargs):
        return submit_form(form, open_http=self._open_http, **kwargs)


class WSGIInterceptingBrowser(Browser):
    """A Browser that uses wsgi-intercept to blah blah."""

    def __init__(self, wsgi_app_creator):
        """
        @param wsgi_app_creator: wsgi app (ie two arg callable)
        """
        self._cookiejar = cookielib.CookieJar()
        self._opener = urllib2.build_opener(WSGI_HTTPHandler(), urllib2.HTTPCookieProcessor(self._cookiejar))
        wsgi_intercept.add_wsgi_intercept('localhost', 80, lambda:wsgi_app_creator)
        self._tweak_user_agent(self._opener)
        self.url = None
        self.contents = None
        self.history = []
