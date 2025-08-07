"""
Link processing for WikiExtractor
Handles internal and external links
"""
import re
from urllib.parse import quote as urlencode
from ..utils.regex_patterns import (
    EXT_LINK_BRACKETED_RE, EXT_IMAGE_RE, TAIL_RE
)
from ..utils.text_utils import find_balanced
from ..config.settings import ACCEPTED_NAMESPACES


def replace_external_links(text):
    """
    Replace external links with appropriate format.

    Args:
        text: Text containing external links

    Returns:
        Text with external links processed
    """
    result = ''
    cur = 0

    for match in EXT_LINK_BRACKETED_RE.finditer(text):
        result += text[cur:match.start()]
        cur = match.end()

        url = match.group(1)
        label = match.group(3)

        # Check if the label is an image URL
        if EXT_IMAGE_RE.match(label):
            label = make_external_image(label)

        result += make_external_link(url, label)

    return result + text[cur:]


def make_external_link(url, anchor, keep_links=False):
    """
    Format external link based on settings.

    Args:
        url: URL of the link
        anchor: Anchor text
        keep_links: Whether to preserve HTML links

    Returns:
        Formatted link
    """
    if keep_links:
        return f'<a href="{urlencode(url)}">{anchor}</a>'
    else:
        return anchor


def make_external_image(url, alt='', keep_links=False):
    """
    Format external image based on settings.

    Args:
        url: URL of the image
        alt: Alt text
        keep_links: Whether to preserve HTML images

    Returns:
        Formatted image
    """
    if keep_links:
        return f'<img src="{url}" alt="{alt}">'
    else:
        return alt


def replace_internal_links(text):
    """
    Replace internal links (wikilinks) with appropriate format.

    Args:
        text: Text containing internal links

    Returns:
        Text with internal links processed
    """
    cur = 0
    result = ''

    for start, end in find_balanced(text, ['[['], [']]']):
        # Check for trailing text (like 's' for plural)
        match = TAIL_RE.match(text, end)
        if match:
            trail = match.group(0)
            end_pos = match.end()
        else:
            trail = ''
            end_pos = end

        inner = text[start + 2:end - 2]

        # Find first pipe separator
        pipe = inner.find('|')
        if pipe < 0:
            title = inner
            label = title
        else:
            title = inner[:pipe].rstrip()
            # Find last pipe (in case of nested links)
            curp = pipe + 1
            for s1, e1 in find_balanced(inner, ['[['], [']]']):
                last = inner.rfind('|', curp, s1)
                if last >= 0:
                    pipe = last
                curp = e1
            label = inner[pipe + 1:].strip()

        result += text[cur:start] + make_internal_link(title, label) + trail
        cur = end_pos

    return result + text[cur:]


def make_internal_link(title, label, keep_links=False):
    """
    Format internal link based on settings and namespace.

    Args:
        title: Link title
        label: Link label/anchor text
        keep_links: Whether to preserve HTML links

    Returns:
        Formatted link or empty string if filtered out
    """
    # Check namespace filtering
    colon = title.find(':')
    if colon > 0 and title[:colon] not in ACCEPTED_NAMESPACES:
        return ''
    if colon == 0:
        # Handle :File: etc.
        colon2 = title.find(':', colon + 1)
        if colon2 > 1 and title[colon + 1:colon2] not in ACCEPTED_NAMESPACES:
            return ''

    if keep_links:
        return f'<a href="{urlencode(title)}">{label}</a>'
    else:
        return label


# Note: find_balanced function is imported from text_utils