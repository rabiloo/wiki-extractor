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