"""
Main Extractor class for WikiExtractor
Coordinates the extraction process for Wikipedia articles
"""

import logging
import re
from typing import Any

import requests

from .utils.html_clean import drop_nested
from .utils.text_clean import clean_text

# File separator for output
FILE_SEPARATOR: str = '\n'
SECTION_RE: re.Pattern[str] = re.compile(r'(==+)\s*(.*?)\s*\1')

# List formatting for HTML output
LIST_OPEN: dict[str, str] = {'*': '<ul>', '#': '<ol>', ';': '<dl>', ':': '<dl>'}
LIST_CLOSE: dict[str, str] = {'*': '</ul>', '#': '</ol>', ';': '</dl>', ':': '</dl>'}
LIST_ITEM: dict[str, str] = {'*': '<li>%s</li>', '#': '<li>%s</<li>', ';': '<dt>%s</dt>', ':': '<dd>%s</dd>'}

logger = logging.getLogger(__name__)


def get_wikipedia_raw_content(url: str) -> tuple[str, str | None]:
    """Fetch Wikipedia content from URL."""
    # Extract title from URL
    title: str = url.split('/wiki/')[-1].replace('_', ' ')

    # Get page content via API
    api_url: str = "https://en.wikipedia.org/w/api.php"
    params: dict[str, str] = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main'
    }

    try:
        response: requests.Response = requests.get(api_url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch content from {url}: HTTP {response.status_code}")
            return title, None

        data: dict[str, Any] = response.json()
        pages: dict[str, Any] = data['query']['pages']
        page_id: str = list(pages.keys())[0]
        content: str = pages[page_id]['revisions'][0]['slots']['main']['*']

        return title, content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        return title, None


class Extractor:
    """
    An extraction task on an article.
    """
    # Type hints for instance variables
    # template_processor: TemplateProcessor
    discard_sections: set[str]
    keep_links: bool
    keep_sections: bool

    def __init__(
        self,
        title: str,
        keep_links: bool = False,
        keep_sections: bool = True,
        ignore_templates: set[str] = set(),
        discard_templates: set[str] = set(),
        discard_sections: set[str] = set(),
    ) -> None:
        """
        Initialize extractor.
        """
        # Initialize template processor
        # self.template_processor = TemplateProcessor(title, ignore_templates, discard_templates)

        self.discard_sections = discard_sections
        self.keep_links = keep_links
        self.keep_sections = keep_sections

    def _output_markdown(self, text: str, add_markdown_header: bool = False, html_formatting: bool = False) -> str:
        """
        Deal with headers, lists, empty sections, residuals of tables.
            :param text: convert to HTML
        """
        page: list[str] = []  # list of paragraph
        headers: dict[int, str] = {}  # Headers for unfilled sections
        empty_section: bool = False  # empty sections are discarded
        skip_section: bool = False  # sections to discard
        list_level: str = ''  # nesting of lists

        for line in text.split('\n'):
            if not line:
                if len(list_level):  # implies Extractor.HtmlFormatting
                    for c in reversed(list_level):
                        page.append(LIST_CLOSE[c])
                    list_level = ''
                continue

            # Handle section titles
            m: re.Match[str] | None = SECTION_RE.match(line)
            if m:
                title: str = m.group(2)

                # Discard non-desired sections
                if title.lower() in self.discard_sections:
                    skip_section = True
                    empty_section = True
                    continue
                else:
                    skip_section = False

                lev: int = len(m.group(1))
                if html_formatting:
                    page.append("<h%d>%s</h%d>" % (lev, title, lev))
                if title and title[-1] not in '!?':
                    title += '.'

                if add_markdown_header:
                    title = "#" * lev + " " + title

                headers[lev] = title
                # drop previous headers
                headers = {k: v for k, v in headers.items() if k <= lev}
                empty_section = True
                continue

            # Handle non-desired sections content
            if skip_section:
                continue

            # Handle page title
            if line.startswith('++'):
                title = line[2:-2]
                if title:
                    if title[-1] not in '!?':
                        title += '.'
                    page.append(title)
                    continue

            # handle indents  # SOmetimes are indents before lists,etc.
            elif line.startswith(':'):
                # page.append(line.lstrip(':'))
                line = line.lstrip(':')
                if not line:
                    continue

            # handle lists
            #   @see https://www.mediawiki.org/wiki/Help:Formatting
            if line.startswith(('*', '#', ';')):  # lists and enumerations
                if html_formatting:  # HTML output format
                    # close extra levels
                    l_idx: int = 0
                    for c in list_level:
                        if l_idx < len(line) and c != line[l_idx]:
                            for extra in reversed(list_level[l_idx:]):
                                page.append(LIST_CLOSE[extra])
                            list_level = list_level[:l_idx]
                            break
                        l_idx += 1
                    if l_idx < len(line) and line[l_idx] in '*#;:':
                        # add new level (only one, no jumps)
                        # FIXME: handle jumping levels
                        l_type: str = line[l_idx]
                        page.append(LIST_OPEN[l_type])
                        list_level += l_type
                        line = line[l_idx + 1:].strip()
                    else:
                        # continue on same level
                        l_type = list_level[l_idx - 1]
                        line = line[l_idx:].strip()
                    page.append(LIST_ITEM[l_type] % line)
                else:  # txt or json: (maintaining depth levels)
                    # Here the first line in the section is a list
                    if headers:
                        if self.keep_sections:
                            items = sorted(headers.items())
                            page.append('\n')
                            for (_, v) in items:
                                page.append(v)  # header title
                        headers.clear()
                    list_item: str = re.sub('[;#*]', ' ', line)
                    # Fixme? sometimes list before indent: "#:"
                    list_item = re.sub(r"(^ *)(.+)", r"\1- \2", list_item)
                    page.append(list_item)
                    empty_section = False

            elif len(list_level):  # implies Extractor.HtmlFormatting
                for c in reversed(list_level):
                    page.append(LIST_CLOSE[c])
                list_level = ''

            # Drop residuals of lists
            elif line.startswith('{') or line.endswith('}'):
                continue
            # Drop irrelevant lines
            elif (line.startswith('(') and line.endswith(')')) or line.strip('.-') == '':
                continue

            # Write header if not an empty section
            elif headers:
                if self.keep_sections:
                    items = sorted(headers.items())
                    page.append('\n')
                    for (_, v) in items:
                        page.append(v)  # header title
                headers.clear()
                #   here we control a section where there is a list before
                #      text content
                page.append(line)  # first line
                empty_section = False
            elif not empty_section:
                page.append(line)

        content: str = "\n".join(page)
        return content

    def expand_templates(self, wikitext: str, language: str | None = None) -> str | None:
        return self.template_processor.expand_templates(wikitext, language)

    def expand_template(self, body: str, language: str | None = None) -> str | None:
        return self.template_processor.expand_template(body, language)

    def template_params(self, parameters: str) -> list[Any]:
        return self.template_processor.template_params(parameters)

    @property
    def frame(self) -> list[Any]:
        """Get the current template frame stack."""
        return self.template_processor.frame

    def clean_content(
        self,
        text: str,
        add_markdown_header: bool = True,
        html_formatting: bool = False,
        html_safe: bool = True,
    ) -> str:
        """
        Clean and process article text.

        Args:
            text: Raw article text
            add_markdown_header: True to distinguish headers from paragraphs
            expand_templates: Whether to expand templates
            html_safe: Whether to escape HTML entities

        Returns:
            Cleaned text as list of paragraphs
        """
        # Clean the text
        processed_text = drop_nested(text, r'{{', r'}}')

        cleaned_text: str | None = clean_text(processed_text, html_safe, html_formatting)

        if cleaned_text is None:
            return ""

        return self._output_markdown(
            cleaned_text,
            add_markdown_header=add_markdown_header,
            html_formatting=html_formatting
        )
