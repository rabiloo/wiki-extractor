"""
Regular expression patterns used throughout the WikiExtractor
"""
import re
from ..config.settings import URL_PROTOCOLS, SELF_CLOSING_TAGS, IGNORED_TAGS, PLACEHOLDER_TAGS

# Basic patterns
TAIL_RE = re.compile(r'\w+')
SECTION_RE = re.compile(r'(==+)\s*(.*?)\s*\1')
SPACES_RE = re.compile(r' {2,}')
DOTS_RE = re.compile(r'\.{4,}')

# HTML and XML patterns
COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)
SYNTAXHIGHLIGHT_RE = re.compile(r'&lt;syntaxhighlight .*?&gt;(.*?)&lt;/syntaxhighlight&gt;', re.DOTALL)

# Bold and italic patterns
BOLD_ITALIC_RE = re.compile(r"'''''(.*?)'''''")
BOLD_RE = re.compile(r"'''(.*?)'''")
ITALIC_QUOTE_RE = re.compile(r"''\"([^\"]*?)\"''")
ITALIC_RE = re.compile(r"''(.*?)''")
QUOTE_QUOTE_RE = re.compile(r'""([^"]*?)""')

# External link patterns
EXT_LINK_URL_CLASS = r'[^][<>"\x00-\x20\x7F\s]'
EXT_LINK_BRACKETED_RE = re.compile(
    r'\[((' + '|'.join(URL_PROTOCOLS) + ')' + EXT_LINK_URL_CLASS + r'+)\s*([^\]\x00-\x08\x0a-\x1F]*?)\]',
    re.S | re.U | re.I
)

EXT_IMAGE_RE = re.compile(
    r"""^(http://|https://)([^][<>"\x00-\x20\x7F\s]+)
    /([A-Za-z0-9_.,~%\-+&;#*?!=()@\x80-\xFF]+)\.(gif|png|jpg|jpeg)$""",
    re.X | re.S | re.U | re.I
)

# Template and link patterns
TEMPLATE_OPEN_RE = re.compile(r'(?<!{){{(?!{)', re.DOTALL)

# Math processing patterns
MATH_PATTERNS = [
    r'<math(?:\s+display\s*=\s*["\']?block["\']?[^>]*)?>(.+?)</math>',
    r'<math(?:\s[^>]*)?>(.+?)</math>',
    r'&lt;math(?:\s[^&]*?)?&gt;(.+?)&lt;/math&gt;',
    r'\{\{#tag:math\|([^}]+)\}\}'
]

# Create compiled patterns for math
MATH_COMPILED_PATTERNS = [re.compile(pattern, re.DOTALL | re.MULTILINE) for pattern in MATH_PATTERNS]

# Self-closing tag patterns
SELF_CLOSING_PATTERNS = [
    re.compile(r'<\s*%s\b[^>]*/\s*>' % tag, re.DOTALL | re.IGNORECASE)
    for tag in SELF_CLOSING_TAGS
]

# Preformatted lines
PREFORMATTED_RE = re.compile(r'^ .*?$')

# External links (simple patterns)
EXTERNAL_LINK_RE = re.compile(r'\[\w+[^ ]*? (.*?)]')
EXTERNAL_LINK_NO_ANCHOR_RE = re.compile(r'\[\w+[&\]]*\]')

# Entity patterns
ENTITY_RE = re.compile(r"&#?(\w+);")

# Template substitution pattern
TEMPLATE_PARAM_RE = re.compile(r" *([^=']*?) *=(.*)", re.DOTALL)

# Bracket matching patterns
OPEN_BRACES_RE = re.compile(r'[{]{2,}|\[{2,}')
NEXT_BRACES_RE = re.compile(r'[{]{2,}|}{2,}|\[{2,}|]{2,}')

# Language template patterns
LANG_TEMPLATE_RE = re.compile(r'lang\-+', re.IGNORECASE)
LANG_SIMPLE_RE = re.compile(r'lang', re.IGNORECASE)
IPA_TEMPLATE_RE = re.compile(r'IPA', re.IGNORECASE)
SEGLE_TEMPLATE_RE = re.compile(r'segle', re.IGNORECASE)
COORD_TEMPLATE_RE = re.compile(r'coord', re.IGNORECASE)
AUDIO_TEMPLATE_RE = re.compile(r'audio', re.IGNORECASE)

# Special patterns for templates
TEMPLATE_ARG_RE = re.compile(r'\w*(=|:)\w*', re.IGNORECASE)
COORD_DIRECTION_RE = re.compile(r'[NSEW]', re.IGNORECASE)

# Noinclude patterns for templates
NO_INCLUDE_RE = re.compile(r'<noinclude>(?:.*?)</noinclude>', re.DOTALL)
INCLUDE_ONLY_RE = re.compile(r'<includeonly>|</includeonly>', re.DOTALL)
ONLY_INCLUDE_RE = re.compile(r'<onlyinclude>(.*?)</onlyinclude>', re.DOTALL)

# Redirect patterns
REDIRECT_RE = re.compile(r'#REDIRE.*?\[\[([^\]]*)]]', re.IGNORECASE)

# Magic words patterns
MAGIC_WORDS_SWITCHES = (
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

MAGIC_WORDS_RE = re.compile('|'.join(MAGIC_WORDS_SWITCHES))

# Ignored tag patterns (compiled dynamically)
def create_ignored_tag_patterns():
    """Create patterns for ignored HTML tags"""
    patterns = []
    for tag in IGNORED_TAGS:
        left = re.compile(r'<%s\b.*?>' % tag, re.IGNORECASE | re.DOTALL)
        right = re.compile(r'</\s*%s>' % tag, re.IGNORECASE)
        patterns.append((left, right))
    return patterns

IGNORED_TAG_PATTERNS = create_ignored_tag_patterns()

# Placeholder tag patterns
def create_placeholder_tag_patterns():
    """Create patterns for placeholder tags"""
    patterns = []
    for tag, repl in PLACEHOLDER_TAGS.items():
        pattern = re.compile(
            r'<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag),
            re.DOTALL | re.IGNORECASE
        )
        patterns.append((pattern, repl))
    return patterns

PLACEHOLDER_TAG_PATTERNS = create_placeholder_tag_patterns()