import unittest
import main

class TestMainScript(unittest.TestCase):

    def test_check_url(self):
        # Test with URL missing scheme
        self.assertEqual(main.check_url("example.com"), "https://example.com")
        # Test with URL having http scheme
        self.assertEqual(main.check_url("http://example.com"), "http://example.com")
        # Test with URL having https scheme
        self.assertEqual(main.check_url("https://example.com"), "https://example.com")
    
    def test_get_domain(self):
        # Test with URL having http scheme
        self.assertEqual(main.get_domain("http://example.com/path"), "http://example.com")
        # Test with URL having https scheme
        self.assertEqual(main.get_domain("https://example.com/path"), "https://example.com")
        
    
    def test_shortify(self):
        # Test with string longer than 25 characters
        long_str = "This is a very long string that exceeds twenty-five characters."
        self.assertEqual(main.shortify(long_str), "This is a very long strin...")
        # Test with string shorter than 25 characters
        short_str = "Short string"
        self.assertEqual(main.shortify(short_str), "Short string...")
    
    def test_is_page(self):
        # Test with URL having pagination query parameter
        self.assertTrue(main.is_page("https://example.com/products?page=2"))
        # Test with URL having pagination fragment
        self.assertTrue(main.is_page("https://example.com/products#page=3"))
        # Test with URL without pagination
        self.assertFalse(main.is_page("https://example.com/products"))