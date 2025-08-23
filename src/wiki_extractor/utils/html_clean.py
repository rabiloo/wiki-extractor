"""
HTML processing for WikiExtractor
Handles HTML tag processing, formatting, and cleanup
"""

import re
from html.entities import name2codepoint

# Placeholder tags
PLACEHOLDER_TAGS: dict[str, str] = {"math": "formula", "code": "codice"}

# Tags to ignore (keep content, drop tags)
IGNORED_TAGS: tuple[str, ...] = (
    "abbr",
    "b",
    "big",
    "blockquote",
    "center",
    "cite",
    "div",
    "em",
    "font",
    "h1",
    "h2",
    "h3",
    "h4",
    "hiero",
    "i",
    "kbd",
    "nowiki",
    "p",
    "plaintext",
    "s",
    "span",
    "strike",
    "strong",
    "sub",
    "sup",
    "tt",
    "u",
    "var",
)

# Elements to discard from article text
DISCARD_ELEMENTS: list[str] = [
    "gallery",
    "timeline",
    "noinclude",
    "pre",
    "table",
    "tr",
    "td",
    "th",
    "caption",
    "div",
    "form",
    "input",
    "select",
    "option",
    "textarea",
    "ul",
    "li",
    "ol",
    "dl",
    "dt",
    "dd",
    "menu",
    "dir",
    "ref",
    "references",
    "img",
    "imagemap",
    "source",
    "small",
]

# Self-closing HTML tags
SELF_CLOSING_TAGS: tuple[str, ...] = ("br", "hr", "nobr", "ref", "references", "nowiki")

# HTML and XML patterns
BOLD_ITALIC_RE: re.Pattern = re.compile(r"'''''(.*?)'''''")
BOLD_RE: re.Pattern = re.compile(r"'''(.*?)'''")
COMMENT_RE: re.Pattern = re.compile(r"<!--.*?-->", re.DOTALL)
SYNTAXHIGHLIGHT_RE: re.Pattern = re.compile(r"&lt;syntaxhighlight .*?&gt;(.*?)&lt;/syntaxhighlight&gt;", re.DOTALL)

# Bold and italic patterns
ITALIC_QUOTE_RE: re.Pattern = re.compile(r"''\"([^\"]*?)\"''")
ITALIC_RE: re.Pattern = re.compile(r"''(.*?)''")
QUOTE_QUOTE_RE: re.Pattern = re.compile(r'""([^"]*?)""')

# Self-closing tag patterns
SELF_CLOSING_PATTERNS: list[re.Pattern] = [
    re.compile(r"<\s*%s\b[^>]*/\s*>" % tag, re.DOTALL | re.IGNORECASE) for tag in SELF_CLOSING_TAGS
]


# Ignored tag patterns (compiled dynamically)
def _create_ignored_tag_patterns() -> list[tuple[re.Pattern, re.Pattern]]:
    """Create patterns for ignored HTML tags"""
    patterns: list[tuple[re.Pattern, re.Pattern]] = []
    for tag in IGNORED_TAGS:
        left: re.Pattern = re.compile(r"<%s\b.*?>" % tag, re.IGNORECASE | re.DOTALL)
        right: re.Pattern = re.compile(r"</\s*%s>" % tag, re.IGNORECASE)
        patterns.append((left, right))
    return patterns


# Placeholder tag patterns
def _create_placeholder_tag_patterns() -> list[tuple[re.Pattern, str]]:
    """Create patterns for placeholder tags"""
    patterns: list[tuple[re.Pattern, str]] = []
    for tag, repl in PLACEHOLDER_TAGS.items():
        pattern: re.Pattern = re.compile(
            r"<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>" % (tag, tag), re.DOTALL | re.IGNORECASE
        )
        patterns.append((pattern, repl))
    return patterns


IGNORED_TAG_PATTERNS: list[tuple[re.Pattern, re.Pattern]] = _create_ignored_tag_patterns()
PLACEHOLDER_TAG_PATTERNS: list[tuple[re.Pattern, str]] = _create_placeholder_tag_patterns()


def drop_nested(text: str, open_delim: str, close_delim: str) -> str:
    """Remove nested expressions (e.g., templates, tables) from text."""
    open_re: re.Pattern = re.compile(open_delim, re.IGNORECASE)
    close_re: re.Pattern = re.compile(close_delim, re.IGNORECASE)
    spans: list[tuple[int, int]] = []
    nest: int = 0
    start = open_re.search(text, 0)
    if not start:
        return text
    end = close_re.search(text, start.end())
    next_match = start
    while end:
        next_match = open_re.search(text, next_match.end())
        if not next_match:
            while nest:
                nest -= 1
                end0 = close_re.search(text, end.end())
                if end0:
                    end = end0
                else:
                    break
            spans.append((start.start(), end.end()))
            break
        while end.end() < next_match.start():
            if nest:
                nest -= 1
                last = end.end()
                end = close_re.search(text, end.end())
                if not end:
                    span = (spans[0][0], last) if spans else (start.start(), last)
                    spans = [span]
                    break
            else:
                spans.append((start.start(), end.end()))
                start = next_match
                end = close_re.search(text, next_match.end())
                break
        if next_match != start:
            nest += 1
    return _drop_spans(spans, text)


def _unescape(text: str) -> str:
    """
    Remove HTML or XML character references and entities from a text string.

    Args:
        text: The HTML (or XML) source text.

    Returns:
        The plain text, as a Unicode string, if necessary.
    """

    def fixup(match: re.Match) -> str:
        text = match.group(0)
        code = match.group(1)
        try:
            if text[1] == "#":  # character reference
                if text[2] == "x":
                    return chr(int(code[1:], 16))
                else:
                    return chr(int(code))
            else:  # named entity
                return chr(name2codepoint[code])
        except (KeyError, ValueError, OverflowError):
            return text  # leave as is

    return re.sub(r"&#?(\w+);", fixup, text)


def _process_html_formatting(text: str, html_formatting: bool = False) -> str:
    """
    Process bold/italic formatting in text.

    Args:
        text: Text to process
        html_formatting: Whether to use HTML tags or plain text formatting

    Returns:
        Text with formatting applied
    """
    if html_formatting:
        text = BOLD_ITALIC_RE.sub(r"<b>\1</b>", text)
        text = BOLD_RE.sub(r"<b>\1</b>", text)
        text = ITALIC_RE.sub(r"<i>\1</i>", text)
    else:
        text = BOLD_ITALIC_RE.sub(r"\1", text)
        text = BOLD_RE.sub(r"\1", text)
        text = ITALIC_QUOTE_RE.sub(r'"\1"', text)
        text = ITALIC_RE.sub(r'"\1"', text)
        text = QUOTE_QUOTE_RE.sub(r'"\1"', text)

    # Clean up residuals of unbalanced quotes
    text = text.replace("'''", "").replace("''", '"')

    return text


def _process_syntax_highlighting(text: str) -> str:
    """
    Process syntax highlighting tags, preserving their content.

    Args:
        text: Text containing syntax highlighting

    Returns:
        Text with syntax highlighting processed
    """
    result: str = ""
    cur: int = 0

    for match in SYNTAXHIGHLIGHT_RE.finditer(text):
        end: int = match.end()
        result += _unescape(text[cur : match.start()]) + match.group(1)
        cur = end

    result += _unescape(text[cur:])
    return result


def _collect_html_spans(text: str) -> list[tuple[int, int]]:
    """
    Collect spans of HTML elements to be removed.

    Args:
        text: Text to analyze

    Returns:
        List of (start, end) spans to remove
    """
    spans: list[tuple[int, int]] = []

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


def _drop_discarded_elements(text: str) -> str:
    """
    Drop discarded HTML elements from text.

    Args:
        text: Text to process

    Returns:
        Text with discarded elements removed
    """

    for tag in DISCARD_ELEMENTS:
        text = drop_nested(text, r"<\s*%s\b[^>/]*>" % tag, r"<\s*/\s*%s>" % tag)

    return text


def _drop_spans(spans: list[tuple[int, int]], text: str) -> str:
    """
    Drop from text the blocks identified in spans, possibly nested.

    Args:
        spans: List of (start, end) tuples to remove
        text: Source text

    Returns:
        Text with spans removed
    """
    spans.sort()
    result: str = ""
    offset: int = 0
    for start, end in spans:
        if offset <= start:  # Handle nesting
            if offset < start:
                result += text[offset:start]
            offset = end

    result += text[offset:]
    return result


def _expand_placeholders(text: str) -> str:
    """
    Expand placeholder tags in text.

    Args:
        text: Text to process

    Returns:
        Text with placeholders expanded
    """
    for pattern, placeholder in PLACEHOLDER_TAG_PATTERNS:
        index: int = 1
        for match in pattern.finditer(text):
            text = text.replace(match.group(), "%s_%d" % (placeholder, index))
            index += 1

    return text


def clean_html_elements(text: str, html_formatting: bool = False) -> str:
    """
    Process all HTML elements in text.

    Args:
        text: Text to process
        html_formatting: Whether to preserve HTML formatting

    Returns:
        Processed text
    """
    # Process syntax highlighting first
    text = _process_syntax_highlighting(text)

    # Handle bold/italic/quote formatting
    text = _process_html_formatting(text, html_formatting)

    # Collect spans to remove
    spans = _collect_html_spans(text)

    # Bulk remove all spans
    text = _drop_spans(spans, text)

    # Drop discarded elements
    text = _drop_discarded_elements(text)

    if not html_formatting:
        # Turn into text what is left (&amp;nbsp;) and <syntaxhighlight>
        text = _unescape(text)

    # Expand placeholders
    text = _expand_placeholders(text)

    # Replace angle brackets
    text = text.replace("<<", "«").replace(">>", "»")

    return text


def clean_html_entities(text: str) -> str:
    """
    Clean up HTML entities in text.

    Args:
        text: Text to clean

    Returns:
        Text with HTML entities cleaned
    """
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")

    return text
