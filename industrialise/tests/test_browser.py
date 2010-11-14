import unittest
import os
import cgi
from wsgiref.simple_server import make_server
from wsgi_intercept.test_wsgi_app import simple_app
from multiprocessing import Process, Queue

from industrialise import browser

class TestBrowser(unittest.TestCase):
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

class TestPosting(unittest.TestCase):
    # FIXME: THIS IS TERROBLE

    def setUp(self):
        self.q = Queue()
        self.p = Process(target=self.serve, args=(self.q,))
        self.p.start()
        self.port = self.q.get()

    def serve(self, q):
        httpd = make_server('', 0, simple_app_maker(q))
        port = httpd.server_port
        q.put(port)
        httpd.serve_forever()

    def test_whatever(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/localform.html" % os.getcwd()
        b.go(url)
        form = b._tree.forms[0]
        form.fields["username"] = "ROB"
        url = "http://localhost:%s/" % self.port
        b._tree.make_links_absolute(url, resolve_base_href=True)
        response = b.submit(form)
        result = self.q.get()
        print result

    def test_check_code(self):
        b = browser.Browser()
        url = "http://localhost:%s/" % self.port
        b.go(url)
        self.assertEqual(b.response_code, 200)

    def tearDown(self):
        self.p.terminate()

    def test_reload(self):
        b = browser.Browser()
        url = "http://localhost:%s/" % self.port
        b.go(url)
        t = b._tree
        b.reload()
        self.failUnless(t is not b._tree)
        self.assertEqual(b.response_code, 200)

def simple_app_maker(queue):
    def simple_app(environ, start_response):
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
        )
        queue.put('hi')
        print post
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['Hello world!\n']
    return simple_app


class TestWSGIInterception(unittest.TestCase):
    def test_go(self):
        b = browser.WSGIInterceptingBrowser(lambda:simple_app)
        b.go('http://localhost:80/')
        self.assertEqual(b._cur_page, 'WSGI intercept successful!\n')
