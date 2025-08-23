"""
Main Extractor class for WikiExtractor
Coordinates the extraction process for Wikipedia articles
"""

import logging
import re
from typing import Any

import requests

from .utils.text_clean import clean_text

# File separator for output
FILE_SEPARATOR: str = "\n"
SECTION_RE: re.Pattern[str] = re.compile(r"(==+)\s*(.*?)\s*\1")

# List formatting for HTML output
LIST_OPEN: dict[str, str] = {"*": "<ul>", "#": "<ol>", ";": "<dl>", ":": "<dl>"}
LIST_CLOSE: dict[str, str] = {"*": "</ul>", "#": "</ol>", ";": "</dl>", ":": "</dl>"}
LIST_ITEM: dict[str, str] = {"*": "<li>%s</li>", "#": "<li>%s</<li>", ";": "<dt>%s</dt>", ":": "<dd>%s</dd>"}
LIST_ITEM_RE = re.compile(r"^([*#:;]+)\s*(.*)$")

logger = logging.getLogger(__name__)


def get_wikipedia_raw_content(url: str, timeout: int = 30) -> tuple[str, str | None]:
    """Fetch Wikipedia content from URL."""
    # Extract title from URL
    title: str = url.split("/wiki/")[-1].replace("_", " ")

    # Get page content via API
    api_url: str = "https://en.wikipedia.org/w/api.php"
    params: dict[str, str] = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }

    try:
        response: requests.Response = requests.get(api_url, params=params, timeout=timeout)
        if response.status_code != 200:
            logger.error(f"Failed to fetch content from {url}: HTTP {response.status_code}")
            return title, None

        data: dict[str, Any] = response.json()
        pages: dict[str, Any] = data["query"]["pages"]
        page_id: str = list(pages.keys())[0]
        content: str = pages[page_id]["revisions"][0]["slots"]["main"]["*"]

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
        in_list: bool = False  # tracking if we're in a list
        list_stack: list[str] = []  # stack to track nested lists

        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # Skip empty lines but handle list closures
            if not line:
                if in_list:
                    # End current list context
                    in_list = False
                    list_stack = []
                    if page and not page[-1].strip():
                        pass  # Don't add extra empty lines
                    else:
                        page.append("")
                elif not empty_section and page and page[-1].strip():
                    page.append("")  # Add paragraph break
                i += 1
                continue

            # Handle section titles (== Title ==, === Title ===, etc.)
            section_match = SECTION_RE.match(line)
            if section_match:
                title = section_match.group(2).strip()

                # Check if this section should be discarded
                if hasattr(Extractor, "discardSections") and title.lower() in self.discard_sections:
                    skip_section = True
                    empty_section = True
                    i += 1
                    continue
                else:
                    skip_section = False

                # Close any open lists
                if in_list:
                    in_list = False
                    list_stack = []

                level = len(section_match.group(1))

                # Convert to Markdown headers
                if add_markdown_header:
                    # Wikipedia uses = for page title, == for main sections
                    # Convert appropriately to Markdown levels
                    if level == 1:
                        markdown_level = 1  # Main title
                    elif level == 2:
                        markdown_level = 2  # Main sections
                    else:
                        markdown_level = min(level, 6)  # Sub-sections

                    # Add some spacing before headers (except first one)
                    if page and page[-1].strip():
                        page.append("")

                    page.append("#" * markdown_level + " " + title)
                    page.append("")  # Add space after header

                headers[level] = title
                headers = {k: v for k, v in headers.items() if k <= level}
                empty_section = True
                i += 1
                continue

            # Skip content in discarded sections
            if skip_section:
                i += 1
                continue

            # Handle page title markers
            if line.startswith("++") and line.endswith("++"):
                title = line[2:-2].strip()
                if title and add_markdown_header:
                    page.append("# " + title)
                    page.append("")
                empty_section = False
                i += 1
                continue

            # Handle definition lists (;term:definition or ;term followed by :definition)
            if line.startswith(";"):
                if ":" in line:
                    # Term and definition on same line
                    colon_pos = line.find(":")
                    term = line[1:colon_pos].strip()
                    definition = line[colon_pos + 1:].strip()

                    if add_markdown_header:
                        page.append("**" + term + "**")
                        if definition:
                            page.append(definition)
                    else:
                        page.append(term + ": " + definition)
                else:
                    # Term only, definition might follow
                    term = line[1:].strip()
                    if add_markdown_header:
                        page.append("**" + term + "**")
                    else:
                        page.append(term)

                    # Check if next line is a definition
                    if i + 1 < len(lines) and lines[i + 1].startswith(":"):
                        i += 1
                        def_line = lines[i].lstrip(":").strip()
                        if def_line:
                            page.append(def_line)

                in_list = True
                list_stack = ["dl"]
                empty_section = False
                i += 1
                continue

            # Handle blockquotes/indented content (:text)
            elif line.startswith(":") and not line.startswith("::"):
                content = line.lstrip(":").strip()
                if content:
                    # Count indentation level
                    indent_level = len(line) - len(line.lstrip(":"))
                    if add_markdown_header:
                        page.append("> " + content)
                    else:
                        page.append("    " * indent_level + content)
                empty_section = False
                i += 1
                continue

            # Handle lists (* for unordered, # for ordered)
            list_match = LIST_ITEM_RE.match(line)
            if list_match:
                markers = list_match.group(1)
                content = list_match.group(2).strip()

                if not content:
                    i += 1
                    continue

                # Determine list type and depth
                depth = len(markers)
                list_type = markers[-1]  # Last character determines type

                # Handle nested lists
                while len(list_stack) > depth:
                    list_stack.pop()

                while len(list_stack) < depth:
                    if list_type == "*":
                        list_stack.append("ul")
                    elif list_type == "#":
                        list_stack.append("ol")
                    else:
                        list_stack.append("ul")  # Default to unordered

                if not in_list:
                    in_list = True

                # Create appropriate indentation
                indent = "  " * (depth - 1)

                if list_type == "*":
                    marker = "- "
                elif list_type == "#":
                    marker = "1. "
                else:
                    marker = "- "

                # Handle special content patterns
                if "–" in content or "—" in content:
                    # Handle em-dash separated content (common in Wikipedia)
                    dash_char = "–" if "–" in content else "—"
                    parts = content.split(dash_char, 1)
                    if len(parts) == 2:
                        term = parts[0].strip()
                        desc = parts[1].strip()
                        page.append(indent + marker + "**" + term + "** – " + desc)
                    else:
                        page.append(indent + marker + content)
                else:
                    page.append(indent + marker + content)

                empty_section = False
                i += 1
                continue

            # Close any open lists if we encounter non-list content
            if in_list:
                in_list = False
                list_stack = []

            # Handle table remnants and irrelevant markup
            if (
                line.startswith("{|")
                or line.startswith("|}")
                or line.startswith("|-")
                or line.startswith("!")
                or line.startswith("|+")
            ):
                i += 1
                continue

            # Skip lines that are just punctuation or parentheses
            stripped = line.strip()
            if (stripped.startswith("(") and stripped.endswith(")") and len(stripped) > 2) or stripped in [
                "",
                ".",
                "-",
                "--",
                "---",
                "....",
            ]:
                i += 1
                continue

            # Handle regular paragraph content
            if stripped:
                # Add headers if this is the first content in a section
                if len(headers) and empty_section:
                    if hasattr(Extractor, "keepSections") and Extractor.keepSections and not add_markdown_header:
                        items = sorted(headers.items())
                        for level, header_title in items:
                            page.append(header_title)
                    headers.clear()

                # Clean up common Wikipedia artifacts
                cleaned_line = line.strip()

                # Remove file/image references
                cleaned_line = re.sub(r"\[\[File:.*?\]\]", "", cleaned_line)
                cleaned_line = re.sub(r"\[\[Image:.*?\]\]", "", cleaned_line)

                # Handle simple wikilinks [[Link]] or [[Link|Display]]
                cleaned_line = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"[\2](\1)", cleaned_line)
                cleaned_line = re.sub(r"\[\[([^\]]+)\]\]", r"[\1](\1)", cleaned_line)

                # Handle external links [URL Display] or [URL]
                cleaned_line = re.sub(r"\[([^\s\]]+)\s+([^\]]+)\]", r"[\2](\1)", cleaned_line)
                cleaned_line = re.sub(r"\[([^\s\]]+)\]", r"[\1](\1)", cleaned_line)

                # Handle bold/italic markup
                cleaned_line = re.sub(r"'''([^']+)'''", r"**\1**", cleaned_line)  # Bold
                cleaned_line = re.sub(r"''([^']+)''", r"*\1*", cleaned_line)  # Italic

                # Remove template calls {{template}}
                cleaned_line = re.sub(r"\{\{[^}]*\}\}", "", cleaned_line)

                # Remove HTML comments
                cleaned_line = re.sub(r"<!--.*?-->", "", cleaned_line)

                cleaned_line = cleaned_line.strip()

                if cleaned_line:
                    page.append(cleaned_line)
                    empty_section = False

            i += 1

        # Clean up the final output
        result = []
        prev_empty = False

        for line in page:
            is_empty = not line.strip()

            # Avoid multiple consecutive empty lines
            if is_empty and prev_empty:
                continue

            result.append(line)
            prev_empty = is_empty

        # Remove trailing empty lines
        while result and not result[-1].strip():
            result.pop()

        return "\n".join(result)

    # def expand_templates(self, wikitext: str, language: str | None = None) -> str | None:
    #     return self.template_processor.expand_templates(wikitext, language)
    #
    # def expand_template(self, body: str, language: str | None = None) -> str | None:
    #     return self.template_processor.expand_template(body, language)
    #
    # def template_params(self, parameters: str) -> list[Any]:
    #     return self.template_processor.template_params(parameters)

    # @property
    # def frame(self) -> list[Any]:
    #     """Get the current template frame stack."""
    #     return self.template_processor.frame

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
        cleaned_text: str | None = clean_text(text, html_safe, html_formatting)

        if cleaned_text is None:
            return ""

        return self._output_markdown(
            cleaned_text, add_markdown_header=add_markdown_header, html_formatting=html_formatting
        )
