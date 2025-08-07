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
    """Deal with headers, lists, empty sections, residuals of tables.
    :param text: convert to HTML
    """
    # Import here to avoid circular imports
    from ..extractor import Extractor

    page = []  # list of paragraph
    headers = {}  # Headers for unfilled sections
    emptySection = False  # empty sections are discarded
    skipSection = False  #  sections to discard
    listLevel = ''  # nesting of lists
    title = ''

    for line in text.split('\n'):

        if not line:
            if len(listLevel):    # implies Extractor.HtmlFormatting
                for c in reversed(listLevel):
                    page.append(LIST_CLOSE[c])
                    listLevel = ''
            continue

        # Handle section titles
        m = SECTION_RE.match(line)
        if m:
            title = m.group(2)

            # Discard non-desired sections
            if(title.lower() in Extractor.discardSections):
                skipSection = True
                emptySection = True
                continue
            else:
                skipSection = False


            lev = len(m.group(1))
            if Extractor.HtmlFormatting:
                page.append("<h%d>%s</h%d>" % (lev, title, lev))
            if title and title[-1] not in '!?':
                title += '.'

            if mark_headers:
                title = "#"*lev + " " + title

            headers[lev] = title
            # drop previous headers
            headers = { k:v for k,v in headers.items() if k <= lev }
            emptySection = True
            continue

        # Handle non-desired sections content
        if (skipSection):
            continue

        # Handle page title
        if line.startswith('++'):
            title = line[2:-2]
            if title:
                if title[-1] not in '!?':
                    title += '.'
                page.append(title)
                continue

        # handle indents  # SOmetimes are indents before lists,etc.
        elif line[0] == ':':
            #page.append(line.lstrip(':'))
            line = line.lstrip(':')
            if(len(line)<1):
                continue


        # handle lists
        #   @see https://www.mediawiki.org/wiki/Help:Formatting
        #elif line[0] in '*#;': # lists and enumerations
        if line[0] in '*#;': # lists and enumerations
            if Extractor.HtmlFormatting: #HTML output format
                # close extra levels
                l = 0
                for c in listLevel:
                    if l < len(line) and c != line[l]:
                        for extra in reversed(listLevel[l:]):
                            page.append(LIST_CLOSE[extra])
                        listLevel = listLevel[:l]
                        break
                    l += 1
                if l < len(line) and line[l] in '*#;:':
                    # add new level (only one, no jumps)
                    # FIXME: handle jumping levels
                    type = line[l]
                    page.append(LIST_OPEN[type])
                    listLevel += type
                    line = line[l+1:].strip()
                else:
                    # continue on same level
                    type = line[l-1]
                    line = line[l:].strip()
                page.append(LIST_ITEM[type] % line)

            else: # txt or json: (maintaining depth levels)
                # Here the first line in the section is a list
                if len(headers):
                    if Extractor.keepSections:
                        items = sorted(headers.items())
                        page.append('\n')
                        for (i, v) in items:
                            page.append(v) #header title
                    headers.clear()
                list_item = re.sub('[;#\*]',' ', line)
                #Fixme? sometimes list before indent: "#:"
                list_item= re.sub("(^ *)(.+)",r"\1- \2",list_item)
                page.append(list_item)
                emptySection = False



        elif len(listLevel):    # implies Extractor.HtmlFormatting
            for c in reversed(listLevel):
                page.append(LIST_CLOSE[c])
            listLevel = []

        # Drop residuals of lists
        elif line[0] in '{|' or line[-1] == '}':
            continue
        # Drop irrelevant lines
        elif (line[0] == '(' and line[-1] == ')') or line.strip('.-') == '':
            continue


        # Write header if not an empty section
        elif len(headers):
            if Extractor.keepSections:
                items = sorted(headers.items())
                page.append('\n')
                for (i, v) in items:
                    page.append(v) #header title
            headers.clear()
            #   here we control a section where there is a list before
            #      text content
            page.append(line)  # first line
            emptySection = False
        elif not emptySection:
            page.append(line)
            # dangerous
            # # Drop preformatted
            # elif line[0] == ' ':
            #     continue

    return page
