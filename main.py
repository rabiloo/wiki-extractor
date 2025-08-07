"""
Main entry point for WikiExtractor - Full Pipeline Support.
Supports fetching Wikipedia pages from URLs and processing them with command-line arguments.
"""

import sys
import os
import logging
import argparse
import json
import re
from urllib.parse import urlparse, unquote
from wiki_extractor.extractor import Extractor

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False



def extract_title_from_url(url):
    """Extract article title from Wikipedia URL."""
    parsed = urlparse(url)

    # Handle different Wikipedia URL formats
    if '/wiki/' in parsed.path:
        title = parsed.path.split('/wiki/')[-1]
    elif 'title=' in parsed.query:
        # Handle URLs like ?title=Article_Name
        for param in parsed.query.split('&'):
            if param.startswith('title='):
                title = param.split('=', 1)[1]
                break
    else:
        raise ValueError(f"Cannot extract title from URL: {url}")

    # Decode URL encoding and replace underscores with spaces
    title = unquote(title).replace('_', ' ')
    return title


def get_wikipedia_content(url):
    """
    Fetch Wikipedia article content from URL using the Wikipedia API.

    Args:
        url: Wikipedia article URL

    Returns:
        tuple: (article_id, revision_id, title, content, language)
    """
    if not HAS_REQUESTS:
        raise ImportError("requests library is required for fetching Wikipedia content. Install with: pip install requests")

    # Extract title and language from URL
    parsed = urlparse(url)
    language = parsed.netloc.split('.')[0] if '.' in parsed.netloc else 'en'
    title = extract_title_from_url(url)

    # Wikipedia API endpoint
    api_url = f"https://{language}.wikipedia.org/w/api.php"

    # API parameters to get page content
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'revisions|info',
        'rvprop': 'content|ids',
        'inprop': 'url',
        'rvslots': 'main'
    }

    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        if not pages:
            raise ValueError(f"No pages found for title: {title}")

        # Get the first (and should be only) page
        page_data = next(iter(pages.values()))

        if 'missing' in page_data:
            raise ValueError(f"Page not found: {title}")

        # Extract page information
        article_id = str(page_data.get('pageid', ''))
        page_title = page_data.get('title', title)

        # Get revision information
        revisions = page_data.get('revisions', [])
        if not revisions:
            raise ValueError(f"No revisions found for page: {title}")

        revision = revisions[0]
        revision_id = str(revision.get('revid', ''))

        # Get content
        slots = revision.get('slots', {})
        main_slot = slots.get('main', {})
        content = main_slot.get('*', '')

        if not content:
            raise ValueError(f"No content found for page: {title}")

        return article_id, revision_id, page_title, content, language

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch Wikipedia content: {e}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse Wikipedia API response: {e}")


def process_wikipedia_url(url, **kwargs):
    """
    Process a Wikipedia URL and extract clean text.

    Args:
        url: Wikipedia article URL
        **kwargs: Additional processing options

    Returns:
        Processed content based on output format
    """
    # Fetch content from Wikipedia
    article_id, revision_id, title, content, language = get_wikipedia_content(url)

    # Determine base URL
    parsed = urlparse(url)
    url_base = f"{parsed.scheme}://{parsed.netloc}/wiki/"

    # Process based on output format
    output_format = kwargs.get('format', 'text')

    if output_format == 'json':
        return process_article_to_json(
            article_id=article_id,
            revision_id=revision_id,
            url_base=url_base,
            title=title,
            content=content,
            language=language
        )
    else:
        return extract_text(
            article_id=article_id,
            revision_id=revision_id,
            url_base=url_base,
            title=title,
            content=content,
            expand_templates=kwargs.get('expand_templates', False),
            markdown=kwargs.get('markdown', False),
            html_safe=kwargs.get('html_safe', True)
        )


def create_extractor(article_id, revision_id, url_base, title, content, metadata=None):
    """
    Create an Extractor instance for processing a Wikipedia article.
    
    Args:
        article_id: Unique identifier for the article
        revision_id: Revision identifier
        url_base: Base URL for the wiki
        title: Article title
        content: Article content (string or list of lines)
        metadata: Optional metadata dictionary
        
    Returns:
        Configured Extractor instance
    """
    if isinstance(content, str):
        content = [content]
    
    return Extractor(
        id=article_id,
        revid=revision_id,
        urlbase=url_base,
        title=title,
        page=content,
        metadata=metadata or {}
    )


def extract_text(article_id, revision_id, url_base, title, content, 
                expand_templates=False, markdown=False, html_safe=True):
    """
    Extract clean text from a Wikipedia article.
    
    Args:
        article_id: Unique identifier for the article
        revision_id: Revision identifier
        url_base: Base URL for the wiki
        title: Article title
        content: Article content (string or list of lines)
        expand_templates: Whether to expand templates
        markdown: Whether to use markdown formatting
        html_safe: Whether to escape HTML entities
        
    Returns:
        List of cleaned text paragraphs
    """
    extractor = create_extractor(article_id, revision_id, url_base, title, content)
    extractor.markdown = markdown
    
    if isinstance(content, str):
        text = content
    else:
        text = ''.join(content)
    
    return extractor.clean_text(
        text, 
        mark_headers=markdown,
        expand_templates=expand_templates,
        html_safe=html_safe
    )


def process_article_to_json(article_id, revision_id, url_base, title, content, 
                           language='en', metadata=None):
    """
    Process an article and return JSON format.
    
    Args:
        article_id: Unique identifier for the article
        revision_id: Revision identifier
        url_base: Base URL for the wiki
        title: Article title
        content: Article content
        language: Language code
        metadata: Optional metadata dictionary
        
    Returns:
        Dictionary in JSON format
    """
    extractor = create_extractor(article_id, revision_id, url_base, title, content, metadata)
    extractor.to_json = True
    extractor.generator = True
    extractor.language = language
    
    from io import StringIO
    output = StringIO()
    result = extractor.extract(output)
    
    return result


def process_article_to_text(article_id, revision_id, url_base, title, content, 
                           language='en', markdown=False):
    """
    Process an article and return plain text format.
    
    Args:
        article_id: Unique identifier for the article
        revision_id: Revision identifier
        url_base: Base URL for the wiki
        title: Article title
        content: Article content
        language: Language code
        markdown: Whether to use markdown formatting
        
    Returns:
        Tuple of (id, title, url, language, text)
    """
    extractor = create_extractor(article_id, revision_id, url_base, title, content)
    extractor.to_txt = True
    extractor.generator = True
    extractor.language = language
    extractor.markdown = markdown
    
    from io import StringIO
    output = StringIO()
    result = extractor.extract(output)
    
    return result


def setup_argument_parser():
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='WikiExtractor - Extract clean text from Wikipedia articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from Wikipedia URL
  python main.py https://en.wikipedia.org/wiki/Python_(programming_language)

  # Extract with markdown formatting
  python main.py https://en.wikipedia.org/wiki/Python_(programming_language) --markdown

  # Extract to JSON format
  python main.py https://en.wikipedia.org/wiki/Python_(programming_language) --format json

  # Extract with template expansion
  python main.py https://en.wikipedia.org/wiki/Python_(programming_language) --expand-templates

  # Save output to file
  python main.py https://en.wikipedia.org/wiki/Python_(programming_language) --output output.txt
        """
    )

    # Input arguments
    parser.add_argument(
        'url',
        help='Wikipedia article URL to process'
    )

    # Output format options
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: stdout)'
    )

    # Processing options
    parser.add_argument(
        '--markdown', '-m',
        action='store_true',
        help='Use markdown formatting for headers'
    )

    parser.add_argument(
        '--expand-templates',
        action='store_true',
        help='Expand MediaWiki templates (slower but more complete)'
    )

    parser.add_argument(
        '--keep-links',
        action='store_true',
        help='Keep internal links in output'
    )

    parser.add_argument(
        '--no-html-safe',
        action='store_true',
        help='Disable HTML entity escaping'
    )

    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    return parser


def main():
    """Main entry point with command-line argument support."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Set up logging
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    try:
        # Configure extractor settings
        Extractor.keepLinks = args.keep_links
        Extractor.keepSections = True
        Extractor.HtmlFormatting = False
        Extractor.discardSections = set()
        Extractor.discardTemplates = set()
        Extractor.ignoreTemplates = set()
        Extractor.markdown = args.markdown

        # Process the Wikipedia URL
        logging.info(f"Processing Wikipedia URL: {args.url}")

        result = process_wikipedia_url(
            args.url,
            format=args.format,
            markdown=args.markdown,
            expand_templates=args.expand_templates,
            html_safe=not args.no_html_safe
        )

        # Format output
        if args.format == 'json':
            output_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            if isinstance(result, list):
                output_text = '\n\n'.join(result)
            else:
                output_text = str(result)

        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            logging.info(f"Output saved to: {args.output}")
        else:
            print(output_text)

        logging.info("Processing completed successfully")

    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
