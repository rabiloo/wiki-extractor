"""
Text cleaning functions for WikiExtractor
Main text processing and cleaning logic
"""

import html
import re
from typing import List

from .html_clean import clean_html_elements, clean_html_entities
from .link_clean import clean_external_links, clean_internal_links
from .math_clean import clean_math_content
from .table_clean import convert_table_to_markdown
from .template_clean import convert_template_to_markdown, parse_template_content

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

MAGIC_WORDS_COMPILED_PATTERN: re.Pattern[str] = re.compile("|".join(MAGIC_WORDS_SWITCHES))
SPACES_COMPILED_PATTERN: re.Pattern[str] = re.compile(r" {2,}")
DOTS_COMPILED_PATTERN: re.Pattern[str] = re.compile(r"\.{4,}")


def _clean_transclusions(
    text: str, open_delim: str = r"{{", close_delim: str = r"}}", preserve_templates: List[str] = None
) -> str:
    """
    Enhanced version that can preserve certain templates and convert them to Markdown.

    Args:
        text: Source text
        open_delim: Opening delimiter pattern
        close_delim: Closing delimiter pattern
        preserve_templates: List of template names to preserve and convert

    Returns:
        Text with nested expressions removed or converted
    """
    if preserve_templates is None:
        preserve_templates = [
            "cite web",
            "cite journal",
            "cite book",
            "cite news",
            "cite magazine",
            "citation",
            "file",
            "image",
            "quote",
            "blockquote",
            "convert",
            "about",
            "var",
            "variable",
            "math",
            "mvar",
            "tmath",
            "texmath",
        ]

    preserve_templates = [name.lower() for name in preserve_templates]

    open_re = re.compile(open_delim, re.IGNORECASE)
    close_re = re.compile(close_delim, re.IGNORECASE)

    replacements = []  # List of (start, end, replacement_text)
    nest = 0
    start = open_re.search(text, 0)

    if not start:
        return text

    end = close_re.search(text, start.end())
    next_match = start

    while end:
        next_match = open_re.search(text, next_match.end())
        if not next_match:
            # Handle remaining nested structures
            while nest:
                nest -= 1
                end0 = close_re.search(text, end.end())
                if end0:
                    end = end0
                else:
                    break

            # Extract and process template content
            template_content = text[start.start() + 2 : end.start()]
            params = parse_template_content(template_content)
            template_name = params.get("_template_name", "")

            if template_name in preserve_templates:
                markdown = convert_template_to_markdown(template_name, params)
                if markdown:
                    replacements.append((start.start(), end.end(), markdown))
                else:
                    replacements.append((start.start(), end.end(), template_content))
            else:
                replacements.append((start.start(), end.end(), template_content))
            break

        while end.end() < next_match.start():
            if nest:
                nest -= 1
                last = end.end()
                end = close_re.search(text, end.end())
                if not end:
                    # Unbalanced - remove everything from start
                    replacements.append((start.start(), last, ""))
                    break
            else:
                # Process this complete template
                template_content = text[start.start() + 2 : end.start()]
                params = parse_template_content(template_content)
                template_name = params.get("_template_name", "")

                if template_name in preserve_templates:
                    markdown = convert_template_to_markdown(template_name, params)
                    if markdown:
                        replacements.append((start.start(), end.end(), markdown))
                    else:
                        replacements.append((start.start(), end.end(), template_content))
                else:
                    replacements.append((start.start(), end.end(), template_content))

                start = next_match
                end = close_re.search(text, next_match.end())
                break

        if next_match != start:
            nest += 1

    # Apply replacements in reverse order to maintain positions
    replacements.sort(reverse=True)
    result = text

    for start_pos, end_pos, replacement in replacements:
        result = result[:start_pos] + replacement + result[end_pos:]

    return result


def _clean_tables(text: str) -> str:
    """Extract and convert wiki tables to markdown."""
    # Pattern to match wiki tables
    pattern = r"\{\|.*?\n\|\}"

    def replace_table(match):
        try:
            return convert_table_to_markdown(match.group(0))
        except Exception as e:
            print(f"Table conversion error: {e}")
            return match.group(0)  # Keep original if conversion fails

    return re.sub(pattern, replace_table, text, flags=re.DOTALL)


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

    # Drop MagicWords behavioral switches
    text = MAGIC_WORDS_COMPILED_PATTERN.sub("", text)

    # Clean transclusions (templates, parser functions)
    text = _clean_transclusions(text, r"{{", r"}}")

    # Extract tables
    text = _clean_tables(text)

    # Process math content
    text = clean_math_content(text)

    # Process HTML elements
    text = clean_html_elements(text, html_formatting)

    # Process links after HTML cleanup
    text = clean_external_links(text)
    text = clean_internal_links(text)

    # Final text cleanup
    # text = _cleanup_text(text, html_safe)

    # Clean HTML entities
    text = clean_html_entities(text)

    # Re-clean links (for some bad formatted chunks)
    text = clean_external_links(text)
    text = clean_internal_links(text)

    return text
