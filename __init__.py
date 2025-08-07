"""
WikiExtractor package - A tool for extracting plain text from Wikipedia dumps.
"""

from .wiki_extractor.extractor import Extractor
from .wiki_extractor.templates.magic_words import MagicWords
from .wiki_extractor.parsers.text_cleaner import clean, compact

__version__ = "3.0.0"
__all__ = ["Extractor", "MagicWords", "clean", "compact"]