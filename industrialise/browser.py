# -*- test-case-name: "industrialise.tests.test_browser" -*-

import urllib
import urllib2
import urlparse
import cookielib
import robotparser

from lxml.html import fromstring, submit_form
import wsgi_intercept
from wsgi_intercept.urllib2_intercept.wsgi_urllib2 import WSGI_HTTPHandler

from industrialise import __version__ as VERSION

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
        self._robots_txt_cache = {}

    def _tweak_user_agent(self, opener):
        """Alter the user agent of the provided opener."""
        headers = dict(opener.addheaders)
        self._user_agent = "%s; (Industrialise %s)" % (headers['User-agent'],
                                                       VERSION)
        headers['User-agent'] = self._user_agent
        opener.addheaders = headers.items()

    def _load_data(self, url):
        """Make the actual request."""
        response = self._opener.open(url)
        self.response_code = response.getcode()
        return response.read(), response.geturl(), response.info()

    def reload(self):
        """Reload the current page.  Does not update the history."""
        self._visit(self.url)

    def go(self, url):
        """Visit the provided url."""
        self._visit(url)
        self.history.append(url)

    def _robots_txt_allows_this(self, url):
        """Check whether the relevant robots.txt allows us to visit the given url."""
        robots_url = self._calculate_robots_txt_url(url)
        if robots_url not in self._robots_txt_cache:
            p = robotparser.RobotFileParser()
            p.set_url(robots_url)
            try:
                contents, _, _ = self._load_data(robots_url)
                p.parse(contents.splitlines())
                self._robots_txt_cache[robots_url] = p
            except IOError:
                self._robots_txt_cache[robots_url] = FourOhFouredRobotsTxt()
        approver = self._robots_txt_cache[robots_url]
        return approver.can_fetch(self._user_agent, url)

    def _visit(self, url):
        """Visit the given url, after checking the robots.txt says it is ok."""
        try:
            if not self._robots_txt_allows_this(url):
                raise ValueError("robots.txt forbids fetching this.")
            self.contents, self.url, self.info = self._load_data(url)
            self._tree = fromstring(self.contents, base_url=self.url)
            self.code = 200
        except urllib2.URLError, e:
            self.code = e.code
            self.contents = ''

    def back(self):
        """Go back one level in the history, removing the current url from the history stack."""
        self.history.pop()
        self._visit(self.history[-1])

    def follow(self, content):
        """Find a link with the given text contents, and follow it.

        <a href="...">Text contents</a>

        Note: if more than one link matches, a ValueError will be raised.
        """
        self._tree.make_links_absolute(self.url, resolve_base_href=True)
        links = self._tree.xpath('//a[text() = $content]', content=content)
        if len(links) < 1:
            raise ValueError("Link matching that text not found.")
        elif len(links) > 1:
            raise ValueError("More than one matching link found.")
        self.go(links[0].attrib['href'])

    def find(self, path):
        """Do an xpath query on the current page, returning a list of lxml Elements that match."""
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

    forms = property(_forms, doc="Form objects from the current page")

    def _calculate_robots_txt_url(self, url):
        """Figure out what the correct robots.txt is for the given url."""
        bits = urlparse.urlparse(url)
        scheme, netloc, _, _, _, _ = bits
        return "%s://%s/robots.txt" % (scheme, netloc)

class FourOhFouredRobotsTxt(object):
    """robotparser stub that always returns True for can_fetch."""

    def can_fetch(self, user_agent, url):
        return True

class Form(object):
    """A trivial wrapper for lxml form objects - these just have a prettier repr."""

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
        self._robots_txt_cache = {}
