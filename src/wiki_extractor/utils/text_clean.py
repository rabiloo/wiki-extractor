"""
Text cleaning functions for WikiExtractor
Main text processing and cleaning logic
"""

import html
import re

from .html_clean import clean_html_elements, clean_html_entities, drop_nested
from .link_clean import clean_external_links, clean_internal_links
from .math_clean import clean_math_content

# Magic words patterns
MAGIC_WORDS_SWITCHES: tuple[str, ...] = (
    '__NOTOC__',
    '__FORCETOC__',
    '__TOC__',
    '__NEWSECTIONLINK__',
    '__NONEWSECTIONLINK__',
    '__NOGALLERY__',
    '__HIDDENCAT__',
    '__NOCONTENTCONVERT__',
    '__NOCC__',
    '__NOTITLECONVERT__',
    '__NOTC__',
    '__START__',
    '__END__',
    '__INDEX__',
    '__NOINDEX__',
    '__STATICREDIRECT__',
    '__DISAMBIG__'
)

MAGIC_WORDS_COMPILED_PATTERN: re.Pattern[str] = re.compile('|'.join(MAGIC_WORDS_SWITCHES))
SPACES_COMPILED_PATTERN: re.Pattern[str] = re.compile(r' {2,}')
DOTS_COMPILED_PATTERN: re.Pattern[str] = re.compile(r'\.{4,}')


def _cleanup_text(text: str, html_safe: bool = True) -> str:
    """
    Perform final text cleanup operations.

    Args:
        text: Text to clean
        html_safe: Whether to escape HTML entities

    Returns:
        Cleaned text
    """
    # Replace tabs with spaces
    text = text.replace('\t', ' ')

    # Normalize spaces
    text = SPACES_COMPILED_PATTERN.sub(' ', text)

    # Normalize dots
    text = DOTS_COMPILED_PATTERN.sub('...', text)

    # Fix punctuation spacing
    text = re.sub(u' (,:\.\)\]»)', r'\1', text)
    text = re.sub(u'(\[\(«) ', r'\1', text)

    # Remove lines with only punctuation
    text = re.sub(r'\n\W+?\n', '\n', text, flags=re.U)

    # Fix comma and period combinations
    text = text.replace(',,', ',').replace(',.', '.')

    if html_safe:
        text = html.escape(text, quote=False)

    return text


def clean_text(text: str, html_safe: bool = True, html_formatting: bool = False) -> str:
    """
    Transform wiki markup into clean text.

    Args:
        text: The text to clean
        html_safe: Whether to convert reserved HTML characters to entities

    Returns:
        The cleaned text
    """
    # Drop tables
    text = drop_nested(text, r'{\|', r'\|}')

    # Drop MagicWords behavioral switches
    text = MAGIC_WORDS_COMPILED_PATTERN.sub('', text)

    # Process math content
    text = clean_math_content(text)

    # Process HTML elements
    text = clean_html_elements(text, html_formatting)

    # Process links after HTML cleanup
    text = clean_external_links(text)
    text = clean_internal_links(text)

    # Final text cleanup
    text = _cleanup_text(text, html_safe)

    # Clean HTML entities
    text = clean_html_entities(text)

    # Re-clean links (for some bad formatted chunks)
    text = clean_external_links(text)
    text = clean_internal_links(text)

    return text
