"""
HTML processing for WikiExtractor
Handles HTML tag processing, formatting, and cleanup
"""

import re
from ..utils.regex_patterns import (
    COMMENT_RE, SYNTAXHIGHLIGHT_RE, SELF_CLOSING_PATTERNS,
    IGNORED_TAG_PATTERNS, PLACEHOLDER_TAG_PATTERNS,
    BOLD_ITALIC_RE, BOLD_RE, ITALIC_QUOTE_RE, ITALIC_RE, QUOTE_QUOTE_RE
)
from ..utils.text_utils import unescape, drop_spans
from ..config.settings import DISCARD_ELEMENTS


def process_html_formatting(text, html_formatting=False):
    """
    Process bold/italic formatting in text.
    
    Args:
        text: Text to process
        html_formatting: Whether to use HTML tags or plain text formatting
        
    Returns:
        Text with formatting applied
    """
    if html_formatting:
        text = BOLD_ITALIC_RE.sub(r'<b>\1</b>', text)
        text = BOLD_RE.sub(r'<b>\1</b>', text)
        text = ITALIC_RE.sub(r'<i>\1</i>', text)
    else:
        text = BOLD_ITALIC_RE.sub(r'\1', text)
        text = BOLD_RE.sub(r'\1', text)
        text = ITALIC_QUOTE_RE.sub(r'"\1"', text)
        text = ITALIC_RE.sub(r'"\1"', text)
        text = QUOTE_QUOTE_RE.sub(r'"\1"', text)
    
    # Clean up residuals of unbalanced quotes
    text = text.replace("'''", '').replace("''", '"')
    
    return text


def process_syntax_highlighting(text):
    """
    Process syntax highlighting tags, preserving their content.
    
    Args:
        text: Text containing syntax highlighting
        
    Returns:
        Text with syntax highlighting processed
    """
    result = ''
    cur = 0
    
    for match in SYNTAXHIGHLIGHT_RE.finditer(text):
        end = match.end()
        result += unescape(text[cur:match.start()]) + match.group(1)
        cur = end
    
    result += unescape(text[cur:])
    return result


def collect_html_spans(text):
    """
    Collect spans of HTML elements to be removed.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of (start, end) spans to remove
    """
    spans = []
    
    # Drop HTML comments
    for match in COMMENT_RE.finditer(text):
        spans.append((match.start(), match.end()))
    
    # Drop self-closing tags
    for pattern in SELF_CLOSING_PATTERNS:
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end()))
    
    # Drop ignored tags
    for left, right in IGNORED_TAG_PATTERNS:
        for match in left.finditer(text):
            spans.append((match.start(), match.end()))
        for match in right.finditer(text):
            spans.append((match.start(), match.end()))
    
    return spans


def drop_discarded_elements(text):
    """
    Drop discarded HTML elements from text.
    
    Args:
        text: Text to process
        
    Returns:
        Text with discarded elements removed
    """
    from ..utils.text_utils import drop_nested
    
    for tag in DISCARD_ELEMENTS:
        text = drop_nested(text, r'<\s*%s\b[^>/]*>' % tag, r'<\s*/\s*%s>' % tag)
    
    return text


def expand_placeholders(text):
    """
    Expand placeholder tags in text.
    
    Args:
        text: Text to process
        
    Returns:
        Text with placeholders expanded
    """
    for pattern, placeholder in PLACEHOLDER_TAG_PATTERNS:
        index = 1
        for match in pattern.finditer(text):
            text = text.replace(match.group(), '%s_%d' % (placeholder, index))
            index += 1
    
    return text


def process_html_elements(text, html_formatting=False):
    """
    Process all HTML elements in text.
    
    Args:
        text: Text to process
        html_formatting: Whether to preserve HTML formatting
        
    Returns:
        Processed text
    """
    # Process syntax highlighting first
    text = process_syntax_highlighting(text)
    
    # Handle bold/italic/quote formatting
    text = process_html_formatting(text, html_formatting)
    
    # Collect spans to remove
    spans = collect_html_spans(text)
    
    # Bulk remove all spans
    text = drop_spans(spans, text)
    
    # Drop discarded elements
    text = drop_discarded_elements(text)
    
    if not html_formatting:
        # Turn into text what is left (&amp;nbsp;) and <syntaxhighlight>
        text = unescape(text)
    
    # Expand placeholders
    text = expand_placeholders(text)
    
    # Replace angle brackets
    text = text.replace('<<', u'«').replace('>>', u'»')
    
    return text


def clean_html_entities(text):
    """
    Clean up HTML entities in text.
    
    Args:
        text: Text to clean
        
    Returns:
        Text with HTML entities cleaned
    """
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    
    return text
