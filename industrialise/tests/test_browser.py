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
        b.go("file://%s/industrialise/tests/valid_html5.html" % os.getcwd())

    def test_finding_something_that_exists(self):
        b = browser.Browser()
        b.go("file://%s/industrialise/tests/valid_html5.html" % os.getcwd())
        self.assertEqual(b.find('//h1')[0].text, "a title")

class TestWithServer(unittest.TestCase):
    def setUp(self):
        
