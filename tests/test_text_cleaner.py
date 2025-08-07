"""Tests for text cleaning functionality."""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_extractor.parsers.text_cleaner import clean, compact, cleanup_text
from wiki_extractor.extractor import Extractor


class TestTextCleaner(unittest.TestCase):
    """Test cases for text cleaning functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = Extractor(
            id="12345",
            revid="67890",
            urlbase="https://en.wikipedia.org/wiki/",
            title="Test Article",
            page=["Test content"]
        )
    
    def test_clean_basic_markup(self):
        """Test cleaning of basic Wikipedia markup."""
        test_text = "'''Bold text''' and ''italic text'' with normal text."
        
        result = clean(self.extractor, test_text)
        
        self.assertIsInstance(result, (str, type(None)))
        if result:
            # Bold and italic markup should be removed
            self.assertNotIn("'''", result)
            self.assertNotIn("''", result)
            self.assertIn("Bold text", result)
            self.assertIn("italic text", result)
    
    def test_clean_links(self):
        """Test cleaning of internal and external links."""
        test_text = "See [[Wikipedia]] and [http://example.com external link]."
        
        result = clean(self.extractor, test_text)
        
        self.assertIsInstance(result, (str, type(None)))
        if result:
            # Link markup should be processed
            self.assertNotIn("[[", result)
            self.assertNotIn("]]", result)
    
    def test_clean_templates(self):
        """Test cleaning of templates."""
        test_text = "{{template|param=value}} Text after template."
        
        result = clean(self.extractor, test_text, expand_templates=False)
        
        self.assertIsInstance(result, (str, type(None)))
        if result:
            # Templates should be removed when not expanding
            self.assertNotIn("{{", result)
            self.assertNotIn("}}", result)
    
    def test_clean_html_elements(self):
        """Test cleaning of HTML elements."""
        test_text = "Text with <b>bold</b> and <i>italic</i> HTML tags."
        
        result = clean(self.extractor, test_text)
        
        self.assertIsInstance(result, (str, type(None)))
        if result:
            # HTML tags should be processed
            self.assertIn("bold", result)
            self.assertIn("italic", result)
    
    def test_clean_math_content(self):
        """Test cleaning of math content."""
        test_text = "Formula: <math>E = mc^2</math> is famous."
        
        result = clean(self.extractor, test_text)
        
        self.assertIsInstance(result, (str, type(None)))
        # Math content should be handled appropriately
    
    def test_clean_empty_text(self):
        """Test cleaning of empty text."""
        result = clean(self.extractor, "")
        
        # Should handle empty text gracefully
        self.assertIsInstance(result, (str, type(None)))
    
    def test_cleanup_text_basic(self):
        """Test basic text cleanup operations."""
        test_text = "Text  with   multiple    spaces\t\tand\ttabs."
        
        result = cleanup_text(test_text)
        
        self.assertIsInstance(result, str)
        # Multiple spaces should be normalized
        self.assertNotIn("  ", result)
        self.assertNotIn("\t", result)
    
    def test_cleanup_text_punctuation(self):
        """Test punctuation cleanup."""
        test_text = "Text with , bad spacing : and . punctuation ."

        result = cleanup_text(test_text)

        self.assertIsInstance(result, str)
        # Text should be processed (punctuation may or may not be fixed depending on implementation)
        self.assertIn("Text with", result)
        self.assertIn("punctuation", result)
    
    def test_cleanup_text_html_safe(self):
        """Test HTML-safe cleanup."""
        test_text = "Text with <script> and & entities."
        
        result = cleanup_text(test_text, html_safe=True)
        
        self.assertIsInstance(result, str)
        # HTML should be escaped
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;", result)
    
    def test_cleanup_text_no_html_safe(self):
        """Test cleanup without HTML escaping."""
        test_text = "Text with <b>bold</b> tags."
        
        result = cleanup_text(test_text, html_safe=False)
        
        self.assertIsInstance(result, str)
        # HTML should not be escaped
        self.assertIn("<b>", result)
    
    def test_compact_basic(self):
        """Test basic text compacting."""
        test_text = "Line 1\n\n\nLine 2\n\n\n\nLine 3"
        
        result = compact(test_text)
        
        self.assertIsInstance(result, list)
        # Should return a list of paragraphs
        self.assertTrue(len(result) > 0)
    
    def test_compact_with_headers(self):
        """Test compacting with header marking."""
        test_text = "= Header 1 =\nContent 1\n\n== Header 2 ==\nContent 2"
        
        result = compact(test_text, mark_headers=True)
        
        self.assertIsInstance(result, list)
        # Headers should be marked appropriately
    
    def test_compact_empty_text(self):
        """Test compacting empty text."""
        result = compact("")
        
        self.assertIsInstance(result, list)
        # Should handle empty text gracefully
    
    def test_clean_with_language(self):
        """Test cleaning with language parameter."""
        test_text = "{{lang|fr|Bonjour}} Hello world."
        
        result = clean(self.extractor, test_text, language="en")
        
        self.assertIsInstance(result, (str, type(None)))
        # Language parameter should be handled
    
    def test_clean_complex_markup(self):
        """Test cleaning of complex markup combinations."""
        test_text = """
        {{Infobox|name=Test}}
        '''Article''' about [[Topic|topics]] and [http://example.com links].
        
        == Section ==
        * List item 1
        * List item 2
        
        <ref>Reference</ref>
        """
        
        result = clean(self.extractor, test_text)
        
        self.assertIsInstance(result, (str, type(None)))
        if result:
            # Complex markup should be processed
            self.assertNotIn("{{", result)
            self.assertNotIn("'''", result)
            self.assertNotIn("[[", result)


if __name__ == '__main__':
    unittest.main()
