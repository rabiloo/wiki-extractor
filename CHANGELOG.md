# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-08-07

### Added
- Complete refactoring of the original WikiExtractor into a modular Python package
- Modular architecture with separate modules for core, parsers, templates, utils, and config
- Comprehensive API with convenience functions for common use cases
- Support for multiple output formats (plain text, JSON, Markdown)
- Improved template processing with dedicated TemplateProcessor class
- Enhanced HTML processing with BeautifulSoup4 integration
- Better error handling and logging throughout the codebase
- Configurable processing options for different use cases
- Type hints and comprehensive docstrings
- Unit test infrastructure
- Professional packaging with setup.py and requirements.txt

### Changed
- Restructured codebase into logical modules for better maintainability
- Improved text cleaning algorithms for better output quality
- Enhanced template expansion with better recursion handling
- Modernized code style and documentation standards

### Fixed
- Various edge cases in text processing and template expansion
- Memory efficiency improvements in large document processing
- Better handling of malformed markup

### Security
- Improved input validation and sanitization
- Better handling of potentially malicious markup

## [2.x.x] - Previous Versions
- Legacy versions of WikiExtractor (not part of this refactored package)

---

## Release Notes

### Version 3.0.0
This is a major refactoring of the WikiExtractor tool, transforming it from a monolithic script into a well-structured Python package. The new version maintains backward compatibility for core functionality while providing a much cleaner API and better extensibility.

Key improvements include:
- **Modular Design**: Clear separation of concerns across different modules
- **Better API**: Easy-to-use functions for common tasks
- **Improved Performance**: More efficient processing algorithms
- **Enhanced Documentation**: Comprehensive documentation and examples
- **Testing**: Full test suite for reliability
- **Packaging**: Professional Python package structure
