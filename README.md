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
"""
Basic usage example for WikiExtractor
Simple demonstration with Wikipedia URL
"""

from wiki_extractor.extractor import Extractor

# Example raw Wikipedia markup (usually fetched via the Wikipedia API)
raw_text = """
{{Short description|Quantum algorithm}}
'''Shor's algorithm''' is a [[quantum algorithm]] for integer factorization...
"""

# Initialize extractor
extractor = Extractor(
    id="1",
    revid="101",
    urlbase="https://en.wikipedia.org/wiki",
    title="Shor's algorithm",
    page=raw_text
)

# Extract clean text (list of paragraphs)
result = extractor.clean_text(raw_text)

print("Number of paragraphs:", len(result))
print("First paragraph:", result[0])

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

## Dependencies

- Python 3.10+

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
