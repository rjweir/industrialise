import unittest
import urllib
import os
import cgi
from wsgi_intercept.test_wsgi_app import simple_app

def build_url_for_file(name):
    return "file://%s/industrialise/tests/html/%s" % (os.getcwd(), name)

class TestBrowser(unittest.TestCase):

    def test_provide_cookiejar(self):
        from industrialise import browser
        sigil = object()
        b = browser.Browser(sigil)
        self.failUnless(sigil is b._cookiejar)

    def test_instantiate(self):
        from industrialise import browser
        browser.Browser()

    def test_load_data(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        data, final_url, info = b._load_data(url)
        from_disk = open("industrialise/tests/html/valid_html5.html").read()
        self.assertEqual(data, from_disk)
        self.assertEqual(final_url, url)
        self.assertEqual(info['Content-length'], str(len(from_disk)))

    def test_going_sets_url_and_loads_page(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        b.go(url)
        self.assertEqual(b.url, url)
        self.assertEqual(b.contents, open(url[6:]).read())

    def test_dupe_links(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        b.go(url)
        self.assertRaises(ValueError, b.follow, "matchme")

    def test_nonexistent_links(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        b.go(url)
        self.assertRaises(ValueError, b.follow, "dontmatchme")

    def test_finding_something_that_exists(self):
        from industrialise import browser
        b = browser.Browser()
        b.go(build_url_for_file("valid_html5.html"))
        self.assertEqual(b.find('//h1')[0].text, "a title")

    def test_finding_something_that_does_not_exist(self):
        from industrialise import browser
        b = browser.Browser()
        b.go(build_url_for_file("valid_html5.html"))
        self.assertEqual(b.find('//h2'), [])

    def testhistory_gets_updated(self):
        from industrialise import browser
        b = browser.Browser()
        url1 = build_url_for_file("valid_html5.html")
        url2 = build_url_for_file("invalid_html5.html")
        b.go(url1)
        b.go(url2)
        self.assertEqual(b.history, [url1, url2])

    def test_visit_once(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        b._visit(url)
        self.assertEqual(b.url, url)
        self.assertEqual(b.contents, open(url[6:]).read())

    def test_visiting_moves(self):
        from industrialise import browser
        b = browser.Browser()
        url1 = build_url_for_file("valid_html5.html")
        url2 = build_url_for_file("invalid_html5.html")
        b.go(url1)
        b.go(url2)
        self.assertEqual(b.url, url2)
        self.assertEqual(b.contents, open(url2[6:]).read())

    def test_step_in_previous_river(self):
        from industrialise import browser
        b = browser.Browser()
        url1 = build_url_for_file("valid_html5.html")
        url2 = build_url_for_file("invalid_html5.html")
        b.go(url1)
        b.go(url2)
        b.back()
        self.assertEqual(b.url, url1)
        self.assertEqual(b.history, [url1])

    def test_reload(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        b.go(url)
        t = b._tree
        b.reload()
        self.failUnless(t is not b._tree)

    def test_follow_link(self):
        from industrialise import browser
        b = browser.Browser()
        url = build_url_for_file("valid_html5.html")
        next_url = build_url_for_file("invalid_html5.html")
        b.go(url)
        t = b._tree
        b.follow("over there")
        self.failUnless(t is not b._tree)
        self.assertEqual(b.url, next_url)
        self.assertEqual(open(next_url[6:]).read(), b.contents)

    def test_tweak_user_agent(self):
        from industrialise import browser
        b = browser.Browser()
        u_a = dict(b._opener.addheaders)['User-agent']
        self.failUnless('Python-urllib' in u_a)
        self.failUnless('Industrialise' in u_a)


class TestWSGIInterception(unittest.TestCase):
    def test_go(self):
        from industrialise import browser
        b = browser.WSGIInterceptingBrowser(simple_app)
        b.go('http://localhost:80/')
        self.assertEqual(b.contents, 'WSGI intercept successful!\n')


class WSGIPostableStub(object):
    """A WSGI app that just stores what gets posted to it."""

    def __init__(self):
        self.post_data = None
        self.map = {
            '/form': open("industrialise/tests/html/localform.html").read()
            }

    def __call__(self, environ, start_response):
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        path = post_env["PATH_INFO"]
        if path in self.map:
            return [self.map[path]]
        self.post_data = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True
            )
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Ack\n']


class DumbWSGIResponder(object):
    """A WSGI app that just returns the provided status, headers and body."""

    def __init__(self, status="200 OK", headers=None, body="Ack."):
        self.status = status
        if headers is None:
            headers = [('Content-type','text/plain')]
        self.headers = headers
        self.body = body

    def __call__(self, environ, start_response):
        start_response(self.status, self.headers)
        return [self.body]


class WSGIHeaderCapturer(object):
    """A WSGI app that just stores the request headers."""

    def __call__(self, environ, start_response):
        self.headers = environ.copy()
        start_response("200 OK", [('Content-Type', 'text/plain')])
        return ["Ack."]


class WSGIStaticServer(object):
    """A WSGI app that just serves a static file."""

    def __call__(self, environ, start_response):
        body = open("industrialise/tests/html/localform.html").read()
        start_response("200 OK", [('Content-Type', 'text/plain')])
        return [body]

class WSGIPostDataReturner(object):
    """A WSGI app that returns posted data in the response body."""

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            return [open("industrialise/tests/html/localform.html").read()]
        else:
            return [environ['wsgi.input'].read()]

class WSGIPostDataReturnerThatRedirects(object):
    """A WSGI app that returns posted data in the response body."""

    def __init__(self):
        self.response = None

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/ENDPOINT':
            start_response("200 OK", [('Content-Type', 'text/plain')])
            return [self.response]
        elif environ['REQUEST_METHOD'] == 'GET':
            start_response('200 OK', [('Content-type', 'text/plain')])
            return [open("industrialise/tests/html/localform.html").read()]
        else:
            start_response('301 Redirect', [('Location', 'http://localhost/ENDPOINT')])
            self.response = environ['wsgi.input'].read()
            return []


class WSGIPostDataReturnerThatRedirectsToA404(object):
    """A WSGI app that takes a POST and then redirects to a 404 page."""

    def __init__(self):
        self.response = None

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/ENDPOINT':
            start_response("200 OK", [('Content-Type', 'text/plain')])
            return [open('industrialise/tests/html/localform.html').read()]
        elif environ['REQUEST_METHOD'] == 'GET':
            start_response('404 Not Found', [('Content-type', 'text/plain')])
            return [open("industrialise/tests/html/localform.html").read()]
        else:
            start_response('301 Redirect', [('Location', 'http://localhost/NOTENDPOINT')])
            self.response = environ['wsgi.input'].read()
            return [open('industrialise/tests/html/localform.html').read()]


class WSGIPostableThatReturnsAPage(object):
    """A WSGI app that takes a POST and returns some data."""

    def __init__(self):
        self.response = None

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            start_response('200 OK', [('Content-type', 'text/plain')])
            return [open("industrialise/tests/html/localform.html").read()]
        else:
            start_response('200 OK', [('Content-type', 'text/plain')])
            return [open("industrialise/tests/html/thirdpage.html").read()]

class WSGICookieSettingServer(object):
    """A WSGI app that just sets a cookie."""

    def __call__(self, environ, start_response):
        headers  =[
            ('Content-type', 'text/plain'),
            ('Set-Cookie', 'ACOOKIE=FOOBAR'),
            ]
        start_response('200 OK', headers)
        return ['Ack.']

class WSGIRedirectingStub(object):
    """A WSGI app that just redirects."""

    def __init__(self, path):
        self.path = path

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == self.path:
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return ['Ack.']
        else:
            status = '301 Redirect'
            response_headers = [('Location', self.path)]
            start_response(status, response_headers)
            return []


class WSGICookieReturningServer(object):
    """A WSGI app that just returns cookies in the response body."""

    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [environ["HTTP_COOKIE"]]


class TestPosting(unittest.TestCase):
    def _getBrowser(self, app=WSGIPostableStub, *args, **kwargs):
        from industrialise import browser
        self._app = app(*args, **kwargs)
        return browser.WSGIInterceptingBrowser(self._app)

    def test_simple_post(self):
        username = "DAUSER"
        b = self._getBrowser()
        url = build_url_for_file("localform.html")
        b.go(url)
        form = b._tree.forms[0]
        form.fields["username"] = username
        url = "http://localhost/"
        b._tree.make_links_absolute(url, resolve_base_href=True)
        response = b.submit(form)
        self.assertEqual(self._app.post_data['username'].value, username)
        self.assertEqual(response.code, 200)

    def test_simple_post_with_extra_bits(self):
        username = "DAUSER"
        b = self._getBrowser()
        url = "http://localhost/form"
        b.go(url)
        form = b._tree.forms[0]
        form.fields["username"] = username
        response = b.submit(form, extra_values={'submit': 'Yes!'})
        self.assertEqual(response.code, 200)
        self.assertEqual(self._app.post_data['username'].value, username)
        self.assertEqual(self._app.post_data['submit'].value, 'Yes!')

    def test_super_simple_scrape(self):
        b = self._getBrowser(WSGIStaticServer)
        url = "http://localhost/"
        b.go(url)
        self.assertEqual(b.find("//head/title")[0].text, "Some HTML5")

    def test_redirect(self):
        destination = "/destination"
        url = "http://localhost/"
        b = self._getBrowser(WSGIRedirectingStub, destination)
        b.go(url)
        self.assertEqual(b.url, "http://localhost/destination")
        self.assertEqual(b._tree.base_url, "http://localhost/destination")

    def test_set_code_200(self):
        b = self._getBrowser(DumbWSGIResponder, status="200 OK", body="Ack.")
        url = "http://localhost/form"
        b.go(url)
        self.assertEqual(b.code, 200)
        self.assertEqual(b.contents, "Ack.")

    def test_set_code_404(self):
        b = self._getBrowser(DumbWSGIResponder, "404")
        url = "http://localhost/form"
        b.go(url)
        self.assertEqual(b.code, 404)

    def test_set_ua(self):
        b = self._getBrowser(WSGIHeaderCapturer)
        url = "http://localhost/"
        b.go(url)
        u_a = self._app.headers['HTTP_USER_AGENT']
        self.failUnless('Industrialise' in u_a)

    def test_GET_form(self):
        username = "DAUSER"
        b = self._getBrowser(WSGIHeaderCapturer)
        url = build_url_for_file("localform.html")
        b.go(url)
        url = "http://localhost/"
        b._tree.make_links_absolute(url, resolve_base_href=True)
        form = b._tree.forms[1]
        form.fields["username"] = username
        url = "http://localhost/"
        b.submit(form)
        self.assertEqual(self._app.headers['QUERY_STRING'],
                         urllib.urlencode([("username", "DAUSER")]))

    def test_contents_set_after_form_submit(self):
        b = self._getBrowser(WSGIPostDataReturner)
        b.go("http://localhost/")
        form = b._tree.forms[0]
        form.fields['username'] = 'someuser'
        b.submit(form)
        self.assertEqual(b.contents, urllib.urlencode([('username', 'someuser')]))

    def test_url_correct_after_form_submit(self):
        b = self._getBrowser(WSGIPostDataReturner)
        b.go("http://localhost/notroot")
        form = b._tree.forms[0]
        form.fields['username'] = 'someuser'
        b.submit(form)
        self.assertEqual(b.url, 'http://localhost/')

    def test_follow_redirect_after_post(self):
        b = self._getBrowser(WSGIPostDataReturnerThatRedirects)
        b.go("http://localhost/notroot")
        form = b._tree.forms[0]
        form.fields['username'] = 'someuser'
        b.submit(form)
        self.assertEqual(b.url, 'http://localhost/ENDPOINT')

    def test_tree_updated_after_post(self):
        b = self._getBrowser(WSGIPostableThatReturnsAPage)
        b.go("http://localhost/notroot")
        form = b._tree.forms[0]
        form.fields['username'] = 'someuser'
        self.assertEqual(len(b.find('//h1[@class="foo"]')), 0)
        b.submit(form)
        self.assertEqual(len(b.find('//h1[@class="foo"]')), 1)

    def test_cookies_end_up_in_cookiejar(self):
        b = self._getBrowser(WSGICookieSettingServer)
        b.go("http://localhost/")
        self.failUnless('ACOOKIE' in b._cookiejar._cookies['localhost.local']['/'])

    def test_we_send_cookies_back(self):
        from industrialise import browser
        b1 = self._getBrowser(WSGICookieSettingServer)
        b1.go("http://localhost/")
        b2 = browser.WSGIInterceptingBrowser(wsgi_app_creator=WSGICookieReturningServer(), cookiejar=b1._cookiejar)
        b2.go("http://localhost/")
        self.assertEqual(b2.contents, 'ACOOKIE=FOOBAR')

    def test_response_code_after_submit(self):
        b = self._getBrowser(WSGIPostDataReturnerThatRedirectsToA404)
        b.go("http://localhost/ENDPOINT")
        form = b._tree.forms[0]
        form.fields['username'] = 'someuser'
        b.submit(form)
        self.assertEqual(b.code, 404)

    def test_info_is_set_after_submission(self):
        pass

    def test_info_is_set_after_load(self):
        pass

    def test_tree_after_failure(self):
        # TODO not sure what should happen
        pass
