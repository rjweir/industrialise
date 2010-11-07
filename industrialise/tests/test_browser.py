import unittest
import os

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
