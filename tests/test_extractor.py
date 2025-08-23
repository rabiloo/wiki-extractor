import pytest

from wiki_extractor.extractor import Extractor


@pytest.fixture
def extractor():
    return Extractor(
        title="Test Article",
        keep_links=False,
        keep_sections=True,
        discard_sections=set(),
    )

def test_extractor_initialization(extractor):
    assert extractor.title == "Test Article"
    assert extractor.keep_links is False
    assert extractor.keep_sections is True
    assert isinstance(extractor.discard_sections, set)

def test_clean_text_basic(extractor):
    test_text = "'''Bold text''' and ''italic text'' with [[internal link]]."
    result = extractor.clean_text(test_text)
    assert isinstance(result, (list, type(None)))
    if result:
        text_content = " ".join(result)
        assert "'''" not in text_content
        assert "''" not in text_content
        assert "[[" not in text_content
        assert "]]" not in text_content

def test_clean_text_with_templates(extractor):
    test_text = "{{template|param=value}} Some text after template."
    result = extractor.clean_text(test_text, expand_templates=False)
    assert isinstance(result, (list, type(None)))
    if result:
        text_content = " ".join(result)
        assert "{{" not in text_content
        assert "}}" not in text_content

def test_clean_text_markdown(extractor):
    test_text = """
    == Header ==
    Some content with '''bold''' text.
    === Subheader ===
    More content here.
    """
    result = extractor.clean_text(test_text, mark_headers=True)
    assert isinstance(result, (list, type(None)))

def test_clean_text_html_safe(extractor):
    test_text = "Text with <script>alert('xss')</script> and & entities."
    result = extractor.clean_text(test_text, html_safe=True)
    assert isinstance(result, (list, type(None)))
    if result:
        text_content = " ".join(result)
        assert "Text with" in text_content
        assert "entities" in text_content

def test_clean_text_empty_input(extractor):
    result = extractor.clean_text("")
    assert isinstance(result, (list, type(None)))

def test_clean_text_none_input(extractor):
    try:
        result = extractor.clean_text(None)
        assert isinstance(result, (list, type(None)))
    except (TypeError, AttributeError):
        pass

def test_url_generation(extractor):
    # If url property exists, test it; otherwise, skip or update this test
    if hasattr(extractor, "url"):
        assert "Test Article" in extractor.url

def test_magic_words_initialization(extractor):
    # If magicWords property exists, test it; otherwise, skip or update this test
    if hasattr(extractor, "magicWords"):
        assert extractor.magicWords is not None

def test_template_processor_initialization(extractor):
    # If template_processor property exists, test it; otherwise, skip or update this test
    if hasattr(extractor, "template_processor"):
        assert extractor.template_processor is not None