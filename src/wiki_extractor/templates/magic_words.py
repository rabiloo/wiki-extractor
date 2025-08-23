"""
MediaWiki Magic Words implementation for WikiExtractor
Handles magic words and behavioral switches
"""

import re

MAGIC_WORDS_NAMES: list[str] = [
    "!",
    "currentmonth",
    "currentmonth1",
    "currentmonthname",
    "currentmonthnamegen",
    "currentmonthabbrev",
    "currentday",
    "currentday2",
    "currentdayname",
    "currentyear",
    "currenttime",
    "currenthour",
    "localmonth",
    "localmonth1",
    "localmonthname",
    "localmonthnamegen",
    "localmonthabbrev",
    "localday",
    "localday2",
    "localdayname",
    "localyear",
    "localtime",
    "localhour",
    "numberofarticles",
    "numberoffiles",
    "numberofedits",
    "articlepath",
    "pageid",
    "sitename",
    "server",
    "servername",
    "scriptpath",
    "stylepath",
    "pagename",
    "pagenamee",
    "fullpagename",
    "fullpagenamee",
    "namespace",
    "namespacee",
    "namespacenumber",
    "currentweek",
    "currentdow",
    "localweek",
    "localdow",
    "revisionid",
    "revisionday",
    "revisionday2",
    "revisionmonth",
    "revisionmonth1",
    "revisionyear",
    "revisiontimestamp",
    "revisionuser",
    "revisionsize",
    "subpagename",
    "subpagenamee",
    "talkspace",
    "talkspacee",
    "subjectspace",
    "subjectspacee",
    "talkpagename",
    "talkpagenamee",
    "subjectpagename",
    "subjectpagenamee",
    "numberofusers",
    "numberofactiveusers",
    "numberofpages",
    "currentversion",
    "rootpagename",
    "rootpagenamee",
    "basepagename",
    "basepagenamee",
    "currenttimestamp",
    "localtimestamp",
    "directionmark",
    "contentlanguage",
    "numberofadmins",
    "cascadingsources",
]

MAGIC_WORDS_SWITCHES: tuple[str, ...] = (
    "__NOTOC__",
    "__FORCETOC__",
    "__TOC__",
    "__NEWSECTIONLINK__",
    "__NONEWSECTIONLINK__",
    "__NOGALLERY__",
    "__HIDDENCAT__",
    "__NOCONTENTCONVERT__",
    "__NOCC__",
    "__NOTITLECONVERT__",
    "__NOTC__",
    "__START__",
    "__END__",
    "__INDEX__",
    "__NOINDEX__",
    "__STATICREDIRECT__",
    "__DISAMBIG__",
)
# Compiled regex for magic word switches
MAGIC_WORDS_COMPILED_PATTERN: re.Pattern[str] = re.compile("|".join(MAGIC_WORDS_SWITCHES))


class MagicWords:
    """
    MediaWiki Magic Words handler.
    One copy in each Extractor.

    @see https://doc.wikimedia.org/mediawiki-core/master/php/MagicWord_8php_source.html
    """

    def __init__(self) -> None:
        """Initialize magic words with default values."""
        self.values: dict[str, str] = {"!": "|"}

    def __getitem__(self, name: str) -> str | None:
        """Get magic word value."""
        return self.values.get(name)

    def __setitem__(self, name: str, value: str) -> None:
        """Set magic word value."""
        self.values[name] = value

    def get(self, name: str, default: str | None = None) -> str | None:
        """Get magic word value with default."""
        return self.values.get(name, default)

    def update(self, values_dict: dict[str, str]) -> None:
        """Update multiple magic word values."""
        self.values.update(values_dict)


def substitute_magic_words(text: str, magic_words: MagicWords) -> str:
    """
    Substitute magic words in text.

    Args:
        text: Text containing magic words
        magic_words: MagicWords instance

    Returns:
        Text with magic words substituted
    """
    # This is a simplified implementation
    # In a full implementation, this would handle all magic word substitutions
    for name in MAGIC_WORDS_NAMES:
        value = magic_words.get(name)
        if value is not None:
            # Simple substitution - in reality this would be more complex
            text = text.replace("{{" + name + "}}", str(value))

    return text


def remove_magic_word_switches(text: str) -> str:
    """
    Remove magic word behavioral switches from text.

    Args:
        text: Text containing magic word switches

    Returns:
        Text with switches removed
    """
    return MAGIC_WORDS_COMPILED_PATTERN.sub("", text)
