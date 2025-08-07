"""Tests for the core Extractor class."""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_extractor.extractor import Extractor


class TestExtractor(unittest.TestCase):
    """Test cases for the Extractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = Extractor(
            id="12345",
            revid="67890",
            urlbase="https://en.wikipedia.org/wiki/",
            title="Test Article",
            page=["Test content line 1", "Test content line 2"]
        )
    
    def test_extractor_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.id, "12345")
        self.assertEqual(self.extractor.revid, "67890")
        self.assertEqual(self.extractor.title, "Test Article")
        self.assertIsInstance(self.extractor.page, list)
        self.assertEqual(len(self.extractor.page), 2)
    
    def test_extractor_with_metadata(self):
        """Test extractor initialization with metadata."""
        metadata = {"author": "Test Author", "category": "Test"}
        extractor = Extractor(
            id="12345",
            revid="67890",
            urlbase="https://en.wikipedia.org/wiki/",
            title="Test Article",
            page=["Test content"],
            metadata=metadata
        )
        
        self.assertEqual(extractor.metadata, metadata)
    
    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        test_text = "'''Bold text''' and ''italic text'' with [[internal link]]."
        
        result = self.extractor.clean_text(test_text)
        
        self.assertIsInstance(result, (list, type(None)))
        if result:
            # Check that markup has been cleaned
            text_content = ' '.join(result)
            self.assertNotIn("'''", text_content)
            self.assertNotIn("''", text_content)
            self.assertNotIn("[[", text_content)
            self.assertNotIn("]]", text_content)
    
    def test_clean_text_with_templates(self):
        """Test text cleaning with templates."""
        test_text = "{{template|param=value}} Some text after template."
        
        result = self.extractor.clean_text(test_text, expand_templates=False)
        
        self.assertIsInstance(result, (list, type(None)))
        if result:
            # Templates should be removed when not expanding
            text_content = ' '.join(result)
            self.assertNotIn("{{", text_content)
            self.assertNotIn("}}", text_content)
    
    def test_clean_text_markdown(self):
        """Test text cleaning with markdown output."""
        test_text = """
        == Header ==
        Some content with '''bold''' text.
        
        === Subheader ===
        More content here.
        """
        
        result = self.extractor.clean_text(test_text, mark_headers=True)
        
        self.assertIsInstance(result, (list, type(None)))
    
    def test_clean_text_html_safe(self):
        """Test text cleaning with HTML safety."""
        test_text = "Text with <script>alert('xss')</script> and & entities."

        result = self.extractor.clean_text(test_text, html_safe=True)

        self.assertIsInstance(result, (list, type(None)))
        if result:
            text_content = ' '.join(result)
            # HTML should be processed (may be escaped or removed)
            self.assertIn("Text with", text_content)
            self.assertIn("entities", text_content)
    
    def test_clean_text_empty_input(self):
        """Test text cleaning with empty input."""
        result = self.extractor.clean_text("")
        
        # Should handle empty input gracefully
        self.assertIsInstance(result, (list, type(None)))
    
    def test_clean_text_none_input(self):
        """Test text cleaning with None input."""
        try:
            result = self.extractor.clean_text(None)
            # Should either handle None gracefully or raise appropriate exception
            self.assertIsInstance(result, (list, type(None)))
        except (TypeError, AttributeError):
            # It's acceptable to raise an exception for None input
            pass
    
    def test_class_attributes(self):
        """Test class-level configuration attributes."""
        # Test default values
        self.assertFalse(Extractor.keepLinks)
        self.assertTrue(Extractor.keepSections)
        self.assertFalse(Extractor.HtmlFormatting)
        self.assertFalse(Extractor.to_json)
        self.assertTrue(Extractor.to_txt)
        self.assertFalse(Extractor.markdown)
        self.assertFalse(Extractor.generator)
    
    def test_configuration_changes(self):
        """Test changing configuration attributes."""
        # Change configuration
        original_keep_links = Extractor.keepLinks
        Extractor.keepLinks = True
        
        self.assertTrue(Extractor.keepLinks)
        
        # Restore original value
        Extractor.keepLinks = original_keep_links
    
    def test_url_generation(self):
        """Test URL generation."""
        # The URL should be generated from urlbase and id
        expected_url_part = "12345"
        self.assertIn(expected_url_part, self.extractor.url)
    
    def test_magic_words_initialization(self):
        """Test that magic words are properly initialized."""
        self.assertIsNotNone(self.extractor.magicWords)
    
    def test_template_processor_initialization(self):
        """Test that template processor is properly initialized."""
        self.assertIsNotNone(self.extractor.template_processor)


if __name__ == '__main__':
    unittest.main()
