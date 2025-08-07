# WikiExtractor

A Python library for extracting clean text from Wikipedia articles. This is a refactored and modularized version of the original WikiExtractor tool, designed to be more maintainable and easier to integrate into other projects.

## Features

- **Clean text extraction** from Wikipedia markup
- **Template expansion** support
- **Multiple output formats**: Plain text, JSON, Markdown
- **Configurable processing** options
- **Modular architecture** for easy customization
- **Language support** for multiple Wikipedia languages
- **HTML entity handling** and cleanup

## Installation

### From Source

```bash
git clone https://github.com/Phongng26/wiki-extractor.git
cd wiki-extractor
pip install -r requirements.txt
```

### Using pip (when published)

```bash
pip install wiki-extractor
```

## Quick Start

### Basic Usage

```python
from wiki_extractor import extract_text

# Extract clean text from a Wikipedia article
article_id = "12345"
revision_id = "67890"
url_base = "https://en.wikipedia.org/wiki/"
title = "Example Article"
content = "{{template}} This is the article content with [[links]] and '''formatting'''."

# Extract clean text
clean_paragraphs = extract_text(
    article_id=article_id,
    revision_id=revision_id,
    url_base=url_base,
    title=title,
    content=content,
    expand_templates=True,
    markdown=False
)

print(clean_paragraphs)
```

### Advanced Usage

```python
from wiki_extractor import Extractor, create_extractor

# Create an extractor instance for more control
extractor = create_extractor(
    article_id="12345",
    revision_id="67890", 
    url_base="https://en.wikipedia.org/wiki/",
    title="Example Article",
    content=["Line 1 of content", "Line 2 of content"]
)

# Configure extraction options
extractor.keepLinks = True
extractor.markdown = True
extractor.language = 'en'

# Extract text with custom settings
text = extractor.clean_text(
    "Article content here",
    mark_headers=True,
    expand_templates=True,
    html_safe=True
)
```

### JSON Output

```python
from wiki_extractor import process_article_to_json

result = process_article_to_json(
    article_id="12345",
    revision_id="67890",
    url_base="https://en.wikipedia.org/wiki/",
    title="Example Article", 
    content="Article content",
    language="en"
)
```

## Configuration

The library provides several configuration options:

- `keepLinks`: Preserve internal links in output
- `keepSections`: Keep section structure
- `HtmlFormatting`: Enable HTML formatting
- `markdown`: Output in Markdown format
- `language`: Target language code
- `discardSections`: Set of section titles to discard
- `discardTemplates`: Set of template names to discard

## Project Structure

```
wiki_extractor/
├── core/                   # Core extraction logic
│   ├── extractor.py       # Main Extractor class
│   └── template_processor.py  # Template processing
├── parsers/               # Text processing modules
│   ├── text_cleaner.py    # Main text cleaning
│   ├── html_processor.py  # HTML element processing
│   ├── link_processor.py  # Link processing
│   └── math_processor.py  # Math formula processing
├── templates/             # Template handling
│   ├── magic_words.py     # MediaWiki magic words
│   └── template_engine.py # Template expansion engine
├── utils/                 # Utility functions
│   ├── text_utils.py      # Text manipulation utilities
│   └── regex_patterns.py  # Compiled regex patterns
├── config/                # Configuration
│   └── settings.py        # Default settings
└── main.py               # Main entry point and convenience functions
```

## Dependencies

- Python 3.6+
- BeautifulSoup4 (for HTML parsing)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

```bash
# Run tests
python -m pytest tests/

# Run tests with coverage
python -m pytest tests/ --cov=wiki_extractor
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the original WikiExtractor by Giuseppe Attardi
- Inspired by the MediaWiki markup processing community

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.
