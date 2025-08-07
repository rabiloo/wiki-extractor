"""Parsers module for WikiExtractor."""

from .text_cleaner import clean, compact
from .html_processor import process_html_elements
from .math_processor import process_text_with_math
from .link_processor import replace_external_links, replace_internal_links