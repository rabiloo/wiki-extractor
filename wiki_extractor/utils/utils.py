import re

def ucfirst(string: str) -> str:
    """Capitalize the first character of a string."""
    if string:
        return string[0].upper() + string[1:] if len(string) > 1 else string.upper()
    return ''

def lcfirst(string: str) -> str:
    """Lowercase the first character of a string."""
    if string:
        return string[0].lower() + string[1:] if len(string) > 1 else string.lower()
    return ''

def normalize_namespace(ns: str) -> str:
    """Normalize a namespace by capitalizing the first character."""
    return ucfirst(ns)

def fully_qualified_template_title(template_title: str, template_prefix: str = '') -> str:
    """Determine the namespace of a template title."""
    if template_title.startswith(':'):
        return ucfirst(template_title[1:])
    match = re.match(r'([^:]*)(:.*)', template_title)
    if match:
        prefix = normalize_namespace(match.group(1))
        if prefix in {'Template'}:
            return f"{prefix}{ucfirst(match.group(2))}"
    return f"{template_prefix}{ucfirst(template_title)}" if template_title else ''

def drop_spans(spans: list, text: str) -> str:
    """Remove identified blocks from text, handling nested spans."""
    spans.sort()
    result = ''
    offset = 0
    for start, end in spans:
        if offset <= start:
            if offset < start:
                result += text[offset:start]
            offset = end
    result += text[offset:]
    return result

def drop_nested(text: str, open_delim: str, close_delim: str) -> str:
    """Remove nested expressions (e.g., templates, tables) from text."""
    open_re = re.compile(open_delim, re.IGNORECASE)
    close_re = re.compile(close_delim, re.IGNORECASE)
    spans = []
    nest = 0
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
    return drop_spans(spans, text)


def balance_brackets(string):
    if (string is None):
        return None
    # Initialize an empty stack to keep track of opening and closing parentheses
    stack = []

    # Iterate over each character in the input string
    for c in string:
        # If the character is an opening parenthesis, push it onto the stack
        if c == '{':
            stack.append(c)
        # If the character is a closing parenthesis
        elif c == '}':
            # If there is at least one opening parenthesis on the stack, pop the most recent one
            if len(stack) > 0 and stack[-1] == '{':
                stack.pop()
            # Otherwise, push the closing parenthesis onto the stack
            else:
                stack.append(c)

    # Count the remaining unbalanced parentheses on the stack
    # and add the appropriate number of opening and closing parentheses
    # to the beginning and end of the output string to balance it.
    return '{' * stack.count('}') + string + '}' * stack.count('(')
