"""
Template processing logic for WikiExtractor
Handles template expansion and processing
"""

import re
import logging
from bs4 import BeautifulSoup
from .utils.text_utils import find_matching_braces, split_parts
from .templates.template_engine import Template, parse_template_parameters
from .config.settings import (
    MAX_TEMPLATE_RECURSION_LEVELS, NOT_EXPAND_TEMPLATES_RE, SUBST_WORDS
)


class TemplateProcessor:
    """
    Handles template expansion and processing for an Extractor.
    """
    
    def __init__(self, extractor):
        """
        Initialize template processor.
        
        Args:
            extractor: The parent Extractor instance
        """
        self.extractor = extractor
        self.frame = []
        self.recursion_exceeded_1_errs = 0  # template recursion within expandTemplates()
        self.recursion_exceeded_2_errs = 0  # template recursion within expandTemplate()
        self.recursion_exceeded_3_errs = 0  # parameter recursion
        self.template_title_errs = 0

    def expand_templates(self, wikitext, language=None):
        """
        Expand templates in wikitext.
        
        Args:
            wikitext: The text to be expanded
            language: Language code
            
        Returns:
            Text with templates expanded, or None if expansion failed
        """
        # Templates are frequently nested. Occasionally, parsing mistakes may
        # cause template insertion to enter an infinite loop, for instance when
        # trying to instantiate Template:Country
        #
        # {{country_{{{1}}}|{{{2}}}|{{{2}}}|size={{{size|}}}|name={{{name|}}}}}
        #
        # which is repeatedly trying to insert template 'country_', which is
        # again resolved to Template:Country. The straightforward solution of
        # keeping track of templates that were already inserted for the current
        # article would not work, because the same template may legally be used
        # more than once, with different parameters in different parts of the
        # article. Therefore, we limit the number of iterations of nested
        # template inclusion.

        result = ''
        if len(self.frame) >= MAX_TEMPLATE_RECURSION_LEVELS:
            self.recursion_exceeded_1_errs += 1
            return None

        cur = 0
        # Look for matching {{...}}
        for s, e in find_matching_braces(wikitext, 2):
            content = self.expand_template(wikitext[s + 2:e - 2], language)
            if content is None:
                # This happens when a template specified in
                # config/discard_templates.txt appears. The whole doc will be discarded.
                return None
            else:
                result += wikitext[cur:s] + content
                cur = e
        
        # Add leftover text
        result += wikitext[cur:]
        return result

    def expand_template(self, body, language=None):
        """
        Expand template invocation.
        
        Args:
            body: The parts of a template
            language: Language code
            
        Returns:
            Expanded template content or None if template should be discarded
        """
        if len(self.frame) >= MAX_TEMPLATE_RECURSION_LEVELS:
            self.recursion_exceeded_2_errs += 1
            return ''

        logging.debug('INVOCATION %d %s', len(self.frame), body)

        parts = split_parts(body)
        title = self.expand_templates(parts[0].strip())

        if title is None:
            # Title included in config/discard_templates.txt
            return None
        elif re.match(NOT_EXPAND_TEMPLATES_RE, title):
            # Don't expand certain templates
            return ''
        elif title.lower() in self.extractor.ignoreTemplates:
            # Not expanding manually specified templates
            return ''
        elif title.lower() in self.extractor.discardTemplates:
            # This whole doc is gonna be discarded
            return None

        # Handle language templates
        if self._handle_language_templates(title, parts):
            return self._process_language_template(title, parts)

        # Handle coordinate templates
        if self._is_coordinate_template(title):
            return self._process_coordinate_template(parts)

        # Handle other special templates
        if self._handle_special_templates(title, parts):
            return self._process_special_template(title, parts)

        # Default template processing
        return self._process_default_template(title, parts, language)

    def _handle_language_templates(self, title, parts):
        """Check if this is a language template."""
        return (title.lower().startswith('lang') or 
                'lang-' in title.lower() or
                title.lower() == 'ipa')

    def _process_language_template(self, title, parts):
        """Process language templates."""
        if len(parts) > 1:
            # Return the content in the target language
            return parts[-1] if parts[-1] else ''
        return ''

    def _is_coordinate_template(self, title):
        """Check if this is a coordinate template."""
        return title.lower() == 'coord'

    def _process_coordinate_template(self, parts):
        """Process coordinate templates."""
        # Simplified coordinate processing
        coords = []
        for part in parts[1:]:  # Skip template name
            if part and not any(x in part.lower() for x in ['display', 'type', 'region']):
                coords.append(part.strip())
        return ' '.join(coords[:4]) if coords else ''

    def _handle_special_templates(self, title, parts):
        """Check if this is a special template that needs custom handling."""
        special_templates = ['convert', 'citation', 'cite', 'reflist', 'nowrap']
        return any(special in title.lower() for special in special_templates)

    def _process_special_template(self, title, parts):
        """Process special templates."""
        if 'convert' in title.lower():
            return self._process_convert_template(parts)
        elif any(x in title.lower() for x in ['citation', 'cite']):
            return self._process_citation_template(parts)
        elif 'reflist' in title.lower():
            return ''  # Remove reference lists
        elif 'nowrap' in title.lower():
            return parts[1] if len(parts) > 1 else ''
        return ''

    def _process_convert_template(self, parts):
        """Process convert templates."""
        if len(parts) >= 3:
            return f"{parts[1]} {parts[2]}"
        return ''

    def _process_citation_template(self, parts):
        """Process citation templates."""
        # Extract basic citation info
        citation_parts = []
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                if key.strip().lower() in ['title', 'author', 'year']:
                    citation_parts.append(value.strip())
        return ' '.join(citation_parts) if citation_parts else ''

    def _process_default_template(self, title, parts, language):
        """Process default template expansion."""
        # This would normally involve looking up the template definition
        # For now, we'll return empty string for unknown templates
        return ''

    def template_params(self, parameters):
        """
        Build a dictionary with positional or name key to expanded parameters.
        
        Args:
            parameters: The parts[1:] of a template, i.e. all except the title
            
        Returns:
            Dictionary of template parameters
        """
        return parse_template_parameters(parameters)
