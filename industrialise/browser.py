# -*- test-case-name: "industrialise.tests.test_browser" -*-

import urllib
import urllib2
import urlparse
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
        # TODO enable debugging using a urllib2.HTTPHandler(debuglevel=1)
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cookiejar))
        self._tweak_user_agent(self._opener)
        self.url = None
        self.contents = None
        self.info = None
        self.code = None
        self.history = []

    def _tweak_user_agent(self, opener):
        headers = dict(opener.addheaders)
        headers['User-agent'] = "%s; (Industrialise %s)" % (headers['User-agent'],
                                                           VERSION)
        opener.addheaders = headers.items()

    def _load_data(self, url):
        response = self._opener.open(url)
        self.response_code = response.getcode()
        return response.read(), response.geturl(), response.info()

    def reload(self):
        self._visit(self.url)

    def go(self, url):
        """Visit the provided url."""
        self._visit(url)
        self.history.append(url)

    def _visit(self, url):
        try:
            self.contents, self.url, self.info = self._load_data(url)
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
        if method in ("POST", "post"):
            return self._opener.open(url, urllib.urlencode(values))
        else:
            return self._opener.open(url_with_query(url, values))

    def submit(self, form, **kwargs):
        try:
            response = submit_form(form._form, open_http=self._open_http, **kwargs)
            self.contents = response.read()
            self.url = response.url
            self._tree = fromstring(self.contents, base_url=self.url)
            self.info = response.info()
            self.code = 200
            return response
        except urllib2.URLError, e:
            self.code = e.code
            self.contents = ''

    def _forms(self):
        return [Form(form) for form in self._tree.forms]

    forms = property(_forms)

class Form(object):
    def __init__(self, form):
        self._form = form
        self.fields = form.fields

    def __repr__(self):
        return "<Form: %s to %s>" % (self._form.method, self._form.action)

def url_with_query(url, values):
     parts = urlparse.urlparse(url)
     rest, (query, frag) = parts[:-2], parts[-2:]
     return urlparse.urlunparse(rest + (urllib.urlencode(values), None))

class WSGIInterceptingBrowser(Browser):
    """A Browser that uses wsgi-intercept to blah blah."""

    def __init__(self, wsgi_app_creator, cookiejar=None):
        """
        @param wsgi_app_creator: wsgi app (ie two arg callable)
        """
        if cookiejar is None:
            cookiejar = cookielib.CookieJar()
        self._cookiejar = cookiejar
        self._opener = urllib2.build_opener(WSGI_HTTPHandler(), urllib2.HTTPCookieProcessor(self._cookiejar))
        wsgi_intercept.add_wsgi_intercept('localhost', 80, lambda:wsgi_app_creator)
        self._tweak_user_agent(self._opener)
        self.url = None
        self.contents = None
        self.history = []
