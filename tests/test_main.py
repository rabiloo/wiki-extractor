"""Tests for main module functions."""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import extract_text, create_extractor, process_article_to_json, process_article_to_text


class TestMainFunctions(unittest.TestCase):
    """Test cases for main module convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_content = """
        '''Test Article''' is a sample article for testing.
        
        == Introduction ==
        This is the introduction section with [[internal link]] and [http://example.com external link].
        
        == Content ==
        * List item 1
        * List item 2
        * List item 3
        
        Some '''bold text''' and ''italic text''.
        """
        
        self.article_id = "12345"
        self.revision_id = "67890"
        self.url_base = "https://en.wikipedia.org/wiki/"
        self.title = "Test Article"
    
    def test_extract_text_basic(self):
        """Test basic text extraction."""
        result = extract_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content
        )
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Check that the result contains expected text
        text_content = ' '.join(result)
        self.assertIn("Test Article", text_content)
        self.assertIn("introduction section", text_content)
    
    def test_extract_text_markdown(self):
        """Test text extraction with markdown formatting."""
        result = extract_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content,
            markdown=True
        )
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    def test_extract_text_with_string_content(self):
        """Test extraction with string content instead of list."""
        content_str = "'''Simple Article''' with some content."
        
        result = extract_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=content_str
        )
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
    
    def test_create_extractor(self):
        """Test extractor creation."""
        extractor = create_extractor(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content
        )
        
        self.assertIsNotNone(extractor)
        self.assertEqual(extractor.id, self.article_id)
        self.assertEqual(extractor.revid, self.revision_id)
        self.assertEqual(extractor.title, self.title)
    
    def test_create_extractor_with_metadata(self):
        """Test extractor creation with metadata."""
        metadata = {"author": "Test Author", "category": "Test"}
        
        extractor = create_extractor(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content,
            metadata=metadata
        )
        
        self.assertIsNotNone(extractor)
        self.assertEqual(extractor.metadata, metadata)
    
    def test_process_article_to_json(self):
        """Test JSON output processing."""
        result = process_article_to_json(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content,
            language="en"
        )
        
        # The result should be a dictionary or tuple depending on implementation
        self.assertIsNotNone(result)
    
    def test_process_article_to_text(self):
        """Test text output processing."""
        result = process_article_to_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=self.sample_content,
            language="en"
        )
        
        # The result should be a tuple or similar structure
        self.assertIsNotNone(result)
    
    def test_empty_content(self):
        """Test handling of empty content."""
        result = extract_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=""
        )
        
        # Should handle empty content gracefully
        self.assertIsInstance(result, (list, type(None)))
    
    def test_malformed_markup(self):
        """Test handling of malformed markup."""
        malformed_content = "'''Unclosed bold and [[unclosed link"
        
        result = extract_text(
            article_id=self.article_id,
            revision_id=self.revision_id,
            url_base=self.url_base,
            title=self.title,
            content=malformed_content
        )
        
        # Should handle malformed markup without crashing
        self.assertIsInstance(result, (list, type(None)))


if __name__ == '__main__':
    unittest.main()
