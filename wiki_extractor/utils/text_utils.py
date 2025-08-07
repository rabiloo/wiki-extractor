"""
Text utility functions for WikiExtractor
"""
import re
from html.entities import name2codepoint
from urllib.parse import quote as urlencode


def get_url(urlbase, uid):
    """Generate URL for a given article ID."""
    return f"{urlbase}?curid={uid}"


def ucfirst(string):
    """Return a string with just its first character uppercase."""
    if string:
        if len(string) > 1:
            return string[0].upper() + string[1:]
        else:
            return string.upper()
    else:
        return ''


def lcfirst(string):
    """Return a string with its first character lowercase."""
    if string:
        if len(string) > 1:
            return string[0].lower() + string[1:]
        else:
            return string.lower()
    else:
        return ''


def normalize_title(title):
    """Normalize Wikipedia page title."""
    # Remove leading/trailing whitespace and underscores
    title = title.strip(' _')
    # Replace sequences of whitespace and underscore chars with a single space
    title = re.sub(r'[\s_]+', ' ', title)

    m = re.match(r'([^:]*):(\s*)(\S(?:.*?))', title)
    if m:
        prefix = m.group(1)
        optional_whitespace = ' ' if m.group(2) else ''
        rest = m.group(3)

        ns = normalize_namespace(prefix)
        from ..config.settings import KNOWN_NAMESPACES
        if ns in KNOWN_NAMESPACES:
            title = ns + ":" + ucfirst(rest)
        else:
            title = ucfirst(prefix) + ":" + optional_whitespace + ucfirst(rest)
    else:
        # No namespace, just capitalize first letter
        title = ucfirst(title)

    return title


def normalize_namespace(ns):
    """Normalize namespace name."""
    return ucfirst(ns)


def unescape(text):
    """
    Remove HTML or XML character references and entities from a text string.

    Args:
        text: The HTML (or XML) source text.

    Returns:
        The plain text, as a Unicode string, if necessary.
    """

    def fixup(match):
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


def balance_brackets(string):
    """Balance curly brackets in a string."""
    if string is None:
        return None

    # Initialize stack to keep track of opening and closing brackets
    stack = []

    # Iterate over each character in the input string
    for c in string:
        if c == '{':
            stack.append(c)
        elif c == '}':
            # If there's a matching opening bracket, remove it
            if len(stack) > 0 and stack[-1] == '{':
                stack.pop()
            else:
                stack.append(c)

    # Balance the string by adding missing brackets
    return '{' * stack.count('}') + string + '}' * stack.count('{')


def drop_spans(spans, text):
    """
    Drop from text the blocks identified in spans, possibly nested.

    Args:
        spans: List of (start, end) tuples to remove
        text: Source text

    Returns:
        Text with spans removed
    """
    spans.sort()
    result = ''
    offset = 0

    for start, end in spans:
        if offset <= start:  # Handle nesting
            if offset < start:
                result += text[offset:start]
            offset = end

    result += text[offset:]
    return result


def drop_nested(text, open_delim, close_delim):
    """
    Drop nested expressions from text (e.g., templates, tables).

    Args:
        text: Source text
        open_delim: Opening delimiter pattern
        close_delim: Closing delimiter pattern

    Returns:
        Text with nested expressions removed
    """
    open_re = re.compile(open_delim, re.IGNORECASE)
    close_re = re.compile(close_delim, re.IGNORECASE)

    spans = []  # pairs (s, e) for each partition
    nest = 0  # nesting level
    start = open_re.search(text, 0)

    if not start:
        return text

    end = close_re.search(text, start.end())
    next_match = start

    while end:
        next_match = open_re.search(text, next_match.end())
        if not next_match:  # termination
            while nest:  # close all pending
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
                if not end:  # unbalanced
                    if spans:
                        span = (spans[0][0], last)
                    else:
                        span = (start.start(), last)
                    spans = [span]
                    break
            else:
                spans.append((start.start(), end.end()))
                start = next_match
                end = close_re.search(text, next_match.end())
                break

        if next_match != start:
            nest += 1

    return drop_spans(spans, text)


def fully_qualified_template_title(template_title, template_prefix='Template:'):
    """
    Determine the namespace of the page being included through the template mechanism.

    Args:
        template_title: Title of the template
        template_prefix: Prefix for templates (usually 'Template:')

    Returns:
        Fully qualified template title
    """
    if template_title.startswith(':'):
        # Leading colon implies main namespace, so strip this colon
        return ucfirst(template_title[1:])
    else:
        m = re.match(r'([^:]*)(:.*)', template_title)
        if m:
            # Check if it designates a known namespace
            prefix = normalize_namespace(m.group(1))
            from ..config.settings import KNOWN_NAMESPACES
            if prefix in KNOWN_NAMESPACES:
                return prefix + ucfirst(m.group(2))

    # Default to Template namespace
    if template_title:
        return template_prefix + ucfirst(template_title)
    else:
        return ''  # Empty title


def find_balanced(text, open_delims, close_delims):
    """
    Find balanced delimiters in text.

    Args:
        text: Text to search
        open_delims: List of opening delimiters
        close_delims: List of closing delimiters

    Returns:
        List of (start, end) positions of balanced delimiters
    """
    spans = []
    stack = []

    i = 0
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
                        open_delim, start = stack.pop()
                        spans.append((start, i + len(delim)))
                    i += len(delim) - 1
                    break
        i += 1

    return spans


def find_matching_braces(text, num_braces):
    """
    Find matching braces in text.

    Args:
        text: Text to search
        num_braces: Number of braces to match (2 for {{, 3 for {{{)

    Returns:
        List of (start, end) positions of matching braces
    """
    open_delim = '{' * num_braces
    close_delim = '}' * num_braces

    spans = []
    stack = []

    i = 0
    while i < len(text):
        if text[i:].startswith(open_delim):
            stack.append(i)
            i += num_braces
        elif text[i:].startswith(close_delim):
            if stack:
                start = stack.pop()
                spans.append((start, i + num_braces))
            i += num_braces
        else:
            i += 1

    return spans


def split_parts(text):
    """
    Split template or function parameters by pipes, respecting nested structures.

    Args:
        text: Text to split

    Returns:
        List of parameter parts
    """
    parts = []
    current = ''
    depth = 0

    i = 0
    while i < len(text):
        char = text[i]

        if char == '{':
            if i + 1 < len(text) and text[i + 1] == '{':
                depth += 1
                current += '{{'
                i += 2
                continue
        elif char == '}':
            if i + 1 < len(text) and text[i + 1] == '}':
                depth -= 1
                current += '}}'
                i += 2
                continue
        elif char == '[':
            if i + 1 < len(text) and text[i + 1] == '[':
                depth += 1
                current += '[['
                i += 2
                continue
        elif char == ']':
            if i + 1 < len(text) and text[i + 1] == ']':
                depth -= 1
                current += ']]'
                i += 2
                continue
        elif char == '|' and depth == 0:
            parts.append(current)
            current = ''
            i += 1
            continue

        current += char
        i += 1

    if current:
        parts.append(current)

    return parts