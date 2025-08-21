"""
Basic usage example for WikiExtractor
Simple demonstration with Wikipedia URL
"""

from wiki_extractor.extractor import Extractor, get_wikipedia_raw_content


def basic_test(url):
    """Simple test function with Wikipedia URL."""

    print("=== Basic WikiExtractor Usage ===\n")

    # Wikipedia URL to test

    print(f"Processing: {url}\n")

    try:
        # Get Wikipedia content
        title, content = get_wikipedia_raw_content(url)

        # Create extractor
        extractor = Extractor(title='Sample Article')

        # Extract clean text
        result = extractor.clean_content(content)

        print("Extraction successful!")
        print(f"Title: {title}")
        print(f"Number of paragraphs: {len(result)}")
        print("\nFirst few paragraphs:")

        # with open('extracted_content.md', 'w', encoding='utf-8') as f:
        #     f.write("\n".join(result))
        # Show first 3 paragraphs
        for i, paragraph in enumerate(result[:3]):
            print(f"{i + 1}. {paragraph[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

    print("\nBasic usage test completed!")


if __name__ == "__main__":
    basic_test(url="https://en.wikipedia.org/wiki/Shor's_algorithm")
