"""
Basic usage example for WikiExtractor
Simple demonstration with Wikipedia URL
"""

from wiki_extractor.extractor import Extractor
import requests

def get_wikipedia_content(url):
    """Fetch Wikipedia content from URL."""
    # Extract title from URL
    title = url.split('/wiki/')[-1].replace('_', ' ')

    # Get page content via API
    api_url = f"https://en.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main'
    }

    response = requests.get(api_url, params=params)
    data = response.json()

    pages = data['query']['pages']
    page_id = list(pages.keys())[0]
    content = pages[page_id]['revisions'][0]['slots']['main']['*']

    return page_id, title, content

def basic_test(url):
    """Simple test function with Wikipedia URL."""

    print("=== Basic WikiExtractor Usage ===\n")

    # Wikipedia URL to test

    print(f"Processing: {url}\n")

    try:
        # Get Wikipedia content
        page_id, title, content = get_wikipedia_content(url)

        # Create extractor
        extractor = Extractor(
            id='123',
            revid='456',
            urlbase='https://en.wikipedia.org/wiki',
            title='Sample Article',
            page=content
        )

        # Extract clean text
        result = extractor.clean_text(content)

        print("Extraction successful!")
        print(f"Title: {title}")
        print(f"Number of paragraphs: {len(result)}")
        print("\nFirst few paragraphs:")

        with open ('extracted_content.md', 'w', encoding='utf-8') as f:
            f.write("\n".join(result))
        # Show first 3 paragraphs
        for i, paragraph in enumerate(result[:3]):
            print(f"{i+1}. {paragraph[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

    print("\nBasic usage test completed!")

if __name__ == "__main__":
    basic_test(url="https://en.wikipedia.org/wiki/Shor's_algorithm")

