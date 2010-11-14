import unittest
import os
import cgi
from wsgi_intercept.test_wsgi_app import simple_app

from industrialise import browser

class TestBrowser(unittest.TestCase):

    def test_provide_cookiejar(self):
        sigil = object()
        b = browser.Browser(sigil)
        self.failUnless(sigil is b._cookiejar)

    def test_instantiate(self):
        browser.Browser()

    def test_load_data(self):
        b = browser.Browser()
        data = b._load_data("file://%s/industrialise/tests/valid_html5.html" % os.getcwd())
        self.assertEqual(data, open("industrialise/tests/valid_html5.html").read())

    def test_go(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        b.go(url)
        self.assertEqual(b._cur_url, url)
        self.assertEqual(b._cur_page, open(url[6:]).read())

    def test_finding_something_that_exists(self):
        b = browser.Browser()
        b.go("file://%s/industrialise/tests/valid_html5.html" % os.getcwd())
        self.assertEqual(b.find('//h1')[0].text, "a title")

    def test_history(self):
        b = browser.Browser()
        url1 = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        url2 = "file://%s/industrialise/tests/invalid_html5.html" % os.getcwd()
        b.go(url1)
        b.go(url2)
        self.assertEqual(b._history, [url1, url2])

    def test_visit_once(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        b._visit(url)
        self.assertEqual(b._cur_url, url)
        self.assertEqual(b._cur_page, open(url[6:]).read())

    def test_visit_twice(self):
        b = browser.Browser()
        url1 = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        url2 = "file://%s/industrialise/tests/invalid_html5.html" % os.getcwd()
        b.go(url1)
        b.go(url2)
        self.assertEqual(b._cur_url, url2)
        self.assertEqual(b._cur_page, open(url2[6:]).read())

    def test_step_in_previous_river(self):
        b = browser.Browser()
        url1 = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        url2 = "file://%s/industrialise/tests/invalid_html5.html" % os.getcwd()
        b.go(url1)
        b.go(url2)
        b.back()
        self.assertEqual(b._cur_url, url1)
        self.assertEqual(b._history, [url1])

    def test_reload(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        b.go(url)
        t = b._tree
        b.reload()
        self.failUnless(t is not b._tree)

    def test_follow_link(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/valid_html5.html" % os.getcwd()
        next_url = "file://%s/industrialise/tests/invalid_html5.html" % os.getcwd()
        b.go(url)
        t = b._tree
        b.follow("over there")
        self.failUnless(t is not b._tree)
        self.assertEqual(b._cur_url, next_url)


class TestWSGIInterception(unittest.TestCase):
    def test_go(self):
        b = browser.WSGIInterceptingBrowser(simple_app)
        b.go('http://localhost:80/')
        self.assertEqual(b._cur_page, 'WSGI intercept successful!\n')


class WSGIPostableStub(object):
    """A WSGI app that just stores what gets posted to it."""

    def __init__(self):
        self.post_data = None

    def __call__(self, environ, start_response):
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        self.post_data = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True
            )
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Ack\n']


class TestPosting(unittest.TestCase):
    def _getBrowser(self):
        self._app = WSGIPostableStub()
        return browser.WSGIInterceptingBrowser(self._app)

    def test_simple_post(self):
        username = "DAUSER"
        b = self._getBrowser()
        url = "file://%s/industrialise/tests/localform.html" % os.getcwd()
        b.go(url)
        form = b._tree.forms[0]
        form.fields["username"] = username
        url = "http://localhost/"
        b._tree.make_links_absolute(url, resolve_base_href=True)
        response = b.submit(form)
        self.assertEqual(self._app.post_data['username'].value, username)
