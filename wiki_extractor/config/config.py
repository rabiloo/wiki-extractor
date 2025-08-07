"""
Configuration settings for WikiExtractor
"""
import re

# File separator for output
FILE_SEPARATOR = '\n'

# Known namespaces
KNOWN_NAMESPACES = {'Template'}

# Elements to discard from article text
DISCARD_ELEMENTS = [
    'gallery', 'timeline', 'noinclude', 'pre',
    'table', 'tr', 'td', 'th', 'caption', 'div',
    'form', 'input', 'select', 'option', 'textarea',
    'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir',
    'ref', 'references', 'img', 'imagemap', 'source', 'small',
]

# Accepted namespaces for internal links
ACCEPTED_NAMESPACES = ['w']

# Templates not to expand (regex patterns)
NOT_EXPAND_TEMPLATES_PATTERNS = [
    """'""",  # Triple quotes from original
    r'^\s+$',  # White spaces
    '!',
    'ISBN',
    'notelist',
    'rp',
    'MF',
    'Pie chart',
    'Graph',
    r'(.*)Infobox(.*)',  # Too complicated to parse
    r'(.*)Infotable(.*)',
    r'(.*)Image(.*)',
    'Flag',
    'pdf',
    'increase',
    'decrease',
    'color',
]

# Compile regex for not expand templates
NOT_EXPAND_TEMPLATES_RE = re.compile('|'.join(NOT_EXPAND_TEMPLATES_PATTERNS), re.IGNORECASE)

# Self-closing HTML tags
SELF_CLOSING_TAGS = ('br', 'hr', 'nobr', 'ref', 'references', 'nowiki')

# Tags to ignore (keep content, drop tags)
IGNORED_TAGS = (
    'abbr', 'b', 'big', 'blockquote', 'center', 'cite', 'div', 'em',
    'font', 'h1', 'h2', 'h3', 'h4', 'hiero', 'i', 'kbd', 'nowiki',
    'p', 'plaintext', 's', 'span', 'strike', 'strong',
    'sub', 'sup', 'tt', 'u', 'var'
)

# Placeholder tags
PLACEHOLDER_TAGS = {'math': 'formula', 'code': 'codice'}

# URL protocols for external links
URL_PROTOCOLS = [
    'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
    'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
    'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
    'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:', '//'
]

# Template recursion limits
MAX_TEMPLATE_RECURSION_LEVELS = 30
MAX_PARAMETER_RECURSION_LEVELS = 16

# Coordinate template auxiliary variables
COORD_AUX_VARS = ["""º""", """'""", """''"""]

# Substitution words
SUBST_WORDS = 'subst:|safesubst:'

# List formatting for HTML output
LIST_OPEN = {'*': '<ul>', '#': '<ol>', ';': '<dl>', ':': '<dl>'}
LIST_CLOSE = {'*': '</ul>', '#': '</ol>', ';': '</dl>', ':': '</dl>'}
LIST_ITEM = {'*': '<li>%s</li>', '#': '<li>%s</<li>', ';': '<dt>%s</dt>', ':': '<dd>%s</dd>'}

# External link URL class pattern
EXT_LINK_URL_CLASS = r'[^][<>"\x00-\x20\x7F\s]'