"""
Text cleaning functions for WikiExtractor
Main text processing and cleaning logic
"""

import re
import html
from ..utils.regex_patterns import MAGIC_WORDS_RE, SECTION_RE, SPACES_RE, DOTS_RE
from ..utils.text_utils import drop_nested
from ..config.settings import LIST_OPEN, LIST_CLOSE, LIST_ITEM
from .math_processor import process_text_with_math
from .html_processor import process_html_elements, clean_html_entities
from .link_processor import replace_external_links, replace_internal_links


def clean(extractor, text, expand_templates=False, language=None, html_safe=True):
    """
    Transform wiki markup into clean text.
    
    Args:
        extractor: The Extractor instance to use
        text: The text to clean
        expand_templates: Whether to perform template expansion
        language: Language code (used if expand_templates is True)
        html_safe: Whether to convert reserved HTML characters to entities
        
    Returns:
        The cleaned text
    """
    if expand_templates:
        # Expand templates
        text = extractor.expandTemplates(text, language)
        if text is None:
            return None
    else:
        # Drop transclusions (templates, parser functions)
        text = drop_nested(text, r'{{', r'}}')

    # Drop tables
    text = drop_nested(text, r'{\|', r'\|}')

    # Drop MagicWords behavioral switches
    text = MAGIC_WORDS_RE.sub('', text)

    # Process math content
    text = process_text_with_math(text)

    # Process HTML elements
    text = process_html_elements(text, extractor.HtmlFormatting)

    # Process links after HTML cleanup
    text = replace_external_links(text)
    text = replace_internal_links(text)

    # Final text cleanup
    text = cleanup_text(text, html_safe)

    # Clean HTML entities
    text = clean_html_entities(text)

    # Re-clean links (for some bad formatted chunks)
    text = replace_external_links(text)
    text = replace_internal_links(text)

    return text


def cleanup_text(text, html_safe=True):
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
    text = SPACES_RE.sub(' ', text)
    
    # Normalize dots
    text = DOTS_RE.sub('...', text)
    
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


def compact(text, mark_headers=False):
    """
    Deal with headers, lists, empty sections, residuals of tables.
    
    Args:
        text: Text to convert
        mark_headers: Whether to mark headers with markdown-style prefixes
        
    Returns:
        List of processed paragraphs
    """
    page = []  # list of paragraphs
    headers = {}  # Headers for unfilled sections
    empty_section = False  # empty sections are discarded
    skip_section = False  # sections to discard
    list_level = ''  # nesting of lists
    title = ''

    for line in text.split('\n'):
        if not line:
            if len(list_level):  # implies Extractor.HtmlFormatting
                for c in reversed(list_level):
                    page.append(LIST_CLOSE[c])
                list_level = ''
            continue

        # Handle section titles
        m = SECTION_RE.match(line)
        if m:
            title = m.group(2)

            # Check if this section should be discarded
            if hasattr(compact, '_discard_sections') and compact._discard_sections:
                if title.lower() in compact._discard_sections:
                    skip_section = True
                    empty_section = True
                    continue
                else:
                    skip_section = False
            
            lev = len(m.group(1))
            if hasattr(compact, '_html_formatting') and compact._html_formatting:
                page.append("<h%d>%s</h%d>" % (lev, title, lev))
            
            if title and title[-1] not in '!?':
                title += '.'

            if mark_headers:
                title = "#" * lev + " " + title

            headers[lev] = title
            # Drop previous headers
            headers = {k: v for k, v in headers.items() if k <= lev}
            empty_section = True
            continue

        # Handle non-desired sections content
        if skip_section:
            continue

        # Handle page title
        if line.startswith('++'):
            title = line[2:-2]
            if title:
                if title[-1] not in '!?':
                    title += '.'
                page.append(title)
                continue

        # Handle indents
        elif line[0] == ':':
            line = line.lstrip(':')
            if len(line) < 1:
                continue

        # Handle lists
        if line[0] in '*#;':
            if hasattr(compact, '_html_formatting') and compact._html_formatting:
                # HTML output format
                l = 0
                for c in list_level:
                    if l < len(line) and c != line[l]:
                        for extra in reversed(list_level[l:]):
                            page.append(LIST_CLOSE[extra])
                        list_level = list_level[:l]
                        break
                    l += 1
                if l < len(line) and line[l] in '*#;:':
                    # Add new level
                    type_char = line[l]
                    page.append(LIST_OPEN[type_char])
                    list_level += type_char
                    line = line[l+1:].strip()
                else:
                    # Continue on same level
                    type_char = line[l-1]
                    line = line[l:].strip()
                page.append(LIST_ITEM[type_char] % line)
            else:
                # Text or JSON format
                if len(headers):
                    if hasattr(compact, '_keep_sections') and compact._keep_sections:
                        items = sorted(headers.items())
                        page.append('\n')
                        for (i, v) in items:
                            page.append(v)
                    headers.clear()
                list_item = re.sub('[;#\*]', ' ', line)
                list_item = re.sub("(^ *)(.+)", r"\1- \2", list_item)
                page.append(list_item)
                empty_section = False

        elif len(list_level):  # implies HTML formatting
            for c in reversed(list_level):
                page.append(LIST_CLOSE[c])
            list_level = []

        # Drop residuals of lists and tables
        elif line[0] in '{|' or line[-1] == '}':
            continue
        # Drop irrelevant lines
        elif (line[0] == '(' and line[-1] == ')') or line.strip('.-') == '':
            continue

        # Write header if not an empty section
        elif len(headers):
            if hasattr(compact, '_keep_sections') and compact._keep_sections:
                items = sorted(headers.items())
                page.append('\n')
                for (i, v) in items:
                    page.append(v)
            headers.clear()
            page.append(line)  # first line
            empty_section = False
        elif not empty_section:
            page.append(line)

    return page
