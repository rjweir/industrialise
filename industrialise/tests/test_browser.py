import unittest

from industrialise import browser

class TestBrowser(unittest.TestCase):
    def test_instantiate(self):
        browser.Browser()
