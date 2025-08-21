"""
Link processing for WikiExtractor
Handles internal and external links
"""
from __future__ import annotations

import re
from urllib.parse import quote as urlencode

# Accepted namespaces for internal links
ACCEPTED_NAMESPACES: list[str] = ['w']

TAIL_RE: re.Pattern[str] = re.compile(r'\w+')

# URL protocols for external links
URL_PROTOCOLS: list[str] = [
    'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
    'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
    'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
    'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:', '//'
]

# External link patterns
EXT_LINK_URL_CLASS: str = r'[^][<>"\x00-\x20\x7F\s]'
EXT_LINK_BRACKETED_RE: re.Pattern[str] = re.compile(
    r'\[((' + '|'.join(URL_PROTOCOLS) + ')' + EXT_LINK_URL_CLASS + r'+)\s*([^\]\x00-\x08\x0a-\x1F]*?)\]',
    re.S | re.U | re.I
)

EXT_IMAGE_RE: re.Pattern[str] = re.compile(
    r"""^(http://|https://)([^][<>"\x00-\x20\x7F\s]+)
    /([A-Za-z0-9_.,~%\-+&;#*?!=()@\x80-\xFF]+)\.(gif|png|jpg|jpeg)$""",
    re.X | re.S | re.U | re.I
)


def _make_external_link(url: str, anchor: str, keep_links: bool = False) -> str:
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


def _make_external_image(url: str, alt: str = '', keep_links: bool = False) -> str:
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


def _make_internal_link(title: str, label: str, keep_links: bool = False) -> str:
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
    colon: int = title.find(':')
    if colon > 0 and title[:colon] not in ACCEPTED_NAMESPACES:
        return ''
    if colon == 0:
        # Handle :File: etc.
        colon2: int = title.find(':', colon + 1)
        if colon2 > 1 and title[colon + 1:colon2] not in ACCEPTED_NAMESPACES:
            return ''

    if keep_links:
        return f'<a href="{urlencode(title)}">{label}</a>'
    else:
        return label


def _find_balanced(text: str, open_delims: list[str], close_delims: list[str]) -> list[tuple[int, int]]:
    """
    Find balanced delimiters in text.

    Args:
        text: Text to search
        open_delims: List of opening delimiters
        close_delims: List of closing delimiters

    Returns:
        List of (start, end) positions of balanced delimiters
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []

    i: int = 0
    while i < len(text):
        # Check for opening delimiters
        for delim in open_delims:
            if text[i:].startswith(delim):
                stack.append((delim, i))
                i += len(delim) - 1
                break
        else:
            # Check for closing delimiters
            for delim in close_delims:
                if text[i:].startswith(delim):
                    if stack:
                        _, start = stack.pop()
                        spans.append((start, i + len(delim)))
                    i += len(delim) - 1
                    break
        i += 1

    return spans


def clean_external_links(text: str) -> str:
    """
    Replace external links with appropriate format.

    Args:
        text: Text containing external links

    Returns:
        Text with external links processed
    """
    result: str = ''
    cur: int = 0

    for match in EXT_LINK_BRACKETED_RE.finditer(text):
        result += text[cur:match.start()]
        cur = match.end()

        url: str = match.group(1)
        label: str = match.group(3)

        # Check if the label is an image URL
        if EXT_IMAGE_RE.match(label):
            label = _make_external_image(label)

        result += _make_external_link(url, label)

    return result + text[cur:]


def clean_internal_links(text: str) -> str:
    """
    Replace internal links (wikilinks) with appropriate format.

    Args:
        text: Text containing internal links

    Returns:
        Text with internal links processed
    """
    cur: int = 0
    result: str = ''

    for start, end in _find_balanced(text, ['[['], [']]']):
        # Check for trailing text (like 's' for plural)
        match: re.Match[str] | None = TAIL_RE.match(text, end)
        if match:
            trail: str = match.group(0)
            end_pos: int = match.end()
        else:
            trail = ''
            end_pos = end

        inner: str = text[start + 2:end - 2]

        # Find first pipe separator
        pipe: int = inner.find('|')
        if pipe < 0:
            title: str = inner
            label: str = title
        else:
            title = inner[:pipe].rstrip()
            # Find last pipe (in case of nested links)
            curp: int = pipe + 1
            for s1, e1 in _find_balanced(inner, ['[['], [']]']):
                last: int = inner.rfind('|', curp, s1)
                if last >= 0:
                    pipe = last
                curp = e1
            label = inner[pipe + 1:].strip()

        result += text[cur:start] + _make_internal_link(title, label) + trail
        cur = end_pos

    return result + text[cur:]
