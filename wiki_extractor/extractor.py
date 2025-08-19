"""
Main Extractor class for WikiExtractor
Coordinates the extraction process for Wikipedia articles
"""

import json
import logging
import time
from .utils.text_utils import get_url
from .templates.magic_words import MagicWords
from .parsers.text_cleaner import clean, compact
from .config.settings import FILE_SEPARATOR
from .template_processor import TemplateProcessor
# ===========================================================================

# Program version
__version__ = "3.0.0"


class Extractor:
    """
    An extraction task on an article.
    """
    
    # Class-level configuration attributes
    keepLinks = False
    keepSections = True
    HtmlFormatting = False
    templatePrefix = ''
    discardSections = set()
    discardTemplates = set()
    ignoreTemplates = set()
    to_json = False
    to_txt = True
    markdown = False
    generator = False
    language = ''

    def __init__(self, id, revid, urlbase, title, page, metadata=None):
        """
        Initialize extractor.
        
        Args:
            id: Article ID
            revid: Revision ID
            urlbase: Base URL for the wiki
            title: Article title
            page: List of lines containing the article content
            metadata: Optional metadata dictionary
        """
        self.id = id
        self.revid = revid
        self.url = get_url(urlbase, id)
        self.title = title
        self.page = page
        self.magicWords = MagicWords()
        self.metadata = metadata or {}
        
        # Initialize template processor
        self.template_processor = TemplateProcessor(self)
        
        # Error counters
        self.recursion_exceeded_1_errs = 0
        self.recursion_exceeded_2_errs = 0
        self.recursion_exceeded_3_errs = 0
        self.template_title_errs = 0

    def clean_text(self, text, mark_headers=False, expand_templates=True, html_safe=True):
        """
        Clean and process article text.
        
        Args:
            text: Raw article text
            mark_headers: True to distinguish headers from paragraphs
            expand_templates: Whether to expand templates
            html_safe: Whether to escape HTML entities
            
        Returns:
            Cleaned text as list of paragraphs
        """
        # Set up magic words
        self._setup_magic_words()

        # Clean the text
        text = clean(self, text, expand_templates=expand_templates,
                    language=self.language, html_safe=html_safe)
        
        if text is None:
            return None
            
        # Compact the text
        text = compact(text, mark_headers=mark_headers)
        return text

    def _setup_magic_words(self):
        """Set up magic words for the current article."""
        self.magicWords['namespace'] = self.title[:max(0, self.title.find(":"))]
        self.magicWords['pagename'] = self.title
        self.magicWords['fullpagename'] = self.title
        self.magicWords['currentyear'] = time.strftime('%Y')
        self.magicWords['currentmonth'] = time.strftime('%m')
        self.magicWords['currentday'] = time.strftime('%d')
        self.magicWords['currenthour'] = time.strftime('%H')
        self.magicWords['currenttime'] = time.strftime('%H:%M:%S')

    def extract(self, out, html_safe=True):
        """
        Extract and save the article.
        
        Args:
            out: Output file handle or path
            html_safe: Whether to escape HTML entities
            
        Returns:
            True if document was processed, False if discarded
        """
        logging.debug("%s\t%s", self.id, self.title)
        
        # Join page content
        text = ''.join(self.page)
        
        # Clean the text
        text = self.clean_text(text, html_safe=html_safe, mark_headers=self.markdown)

        # Check if document should be discarded
        if text is None:
            logging.debug('\t\t\t discarding doc. with title:' + self.title + 
                         ' since it contains a banned template specified in config.')
            return False

        # Insert page title at the beginning
        if self.markdown:
            text.insert(0, '# ' + self.title.split('\n')[0])
        else:
            text.insert(0, self.title.split('\n')[0])

        # Output the document
        if self.to_json:
            return self._output_json(text, out)
        elif self.to_txt:
            return self._output_txt(text, out)
        else:
            return self._output_xml(text, out)

    def _output_json(self, text, out):
        """Output document in JSON format."""
        json_data = {
            'document_id': self.id,
            'title': self.title,
            'url': self.url,
            'language': self.language,
            **self.metadata,
            'text': "\n".join(text),
        }

        if self.generator:
            return json_data
        else:
            out_str = json.dumps(json_data)
            out.write(out_str)
            out.write(FILE_SEPARATOR)
            return True

    def _output_txt(self, text, out):
        """Output document in text format."""
        if self.generator:
            # Return tuple for generator mode
            return self.id, self.title, self.url, self.language, "\n".join(text)
        else:
            out.write("\n".join(text))
            out.write(FILE_SEPARATOR)
            return True

    def _output_xml(self, text, out):
        """Output document in XML format."""
        header = '<doc id="%s" url="%s" title="%s">\n' % (self.id, self.url, self.title)
        header += self.title + '\n\n'
        footer = "\n</doc>\n"
        
        out.write(header)
        out.write('\n'.join(text))
        out.write('\n')
        out.write(footer)
        return True

    def expandTemplates(self, wikitext, language=None):
        """
        Expand templates in wikitext.
        
        Args:
            wikitext: Text containing templates
            language: Language code
            
        Returns:
            Text with templates expanded
        """
        return self.template_processor.expand_templates(wikitext, language)

    def expandTemplate(self, body, language=None):
        """
        Expand a single template.
        
        Args:
            body: Template body
            language: Language code
            
        Returns:
            Expanded template content
        """
        return self.template_processor.expand_template(body, language)

    def templateParams(self, parameters):
        """
        Parse template parameters.
        
        Args:
            parameters: List of parameter strings
            
        Returns:
            Dictionary of parsed parameters
        """
        return self.template_processor.template_params(parameters)

    @property
    def frame(self):
        """Get the current template frame stack."""
        return self.template_processor.frame

    def log_errors(self):
        """Log any errors that occurred during processing."""
        errs = (self.template_title_errs,
                self.recursion_exceeded_1_errs,
                self.recursion_exceeded_2_errs,
                self.recursion_exceeded_3_errs)
        if any(errs):
            logging.debug("Template errors in article '%s' (%s): title(%d) recursion(%d, %d, %d)",
                         self.title, self.id, *errs)
