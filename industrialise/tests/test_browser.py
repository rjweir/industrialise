import unittest
import os
import cgi
from wsgiref.simple_server import make_server
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

class TestPosting(unittest.TestCase):
    def serve(self, q):
        httpd = make_server('', 0, simple_app_maker(q))
        port = httpd.server_port
        q.put(port)
        httpd.handle_request()

    def test_whatever(self):
        b = browser.Browser()
        url = "file://%s/industrialise/tests/localform.html" % os.getcwd()
        b.go(url)
        form = b._tree.forms[0]
        form.fields["username"] = "ROB"
        q = Queue()
        p = Process(target=self.serve, args=(q,))
        p.start()
        port = q.get()
        url = "http://localhost:%s/" % port
        b._tree.make_links_absolute(url, resolve_base_href=True)
        b.submit(form)
        result = q.get()
        print result
        p.join()

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
