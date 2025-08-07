"""
MediaWiki Magic Words implementation for WikiExtractor
Handles magic words and behavioral switches
"""

import re


class MagicWords:
    """
    MediaWiki Magic Words handler.
    One copy in each Extractor.

    @see https://doc.wikimedia.org/mediawiki-core/master/php/MagicWord_8php_source.html
    """
    
    names = [
        '!',
        'currentmonth',
        'currentmonth1',
        'currentmonthname',
        'currentmonthnamegen',
        'currentmonthabbrev',
        'currentday',
        'currentday2',
        'currentdayname',
        'currentyear',
        'currenttime',
        'currenthour',
        'localmonth',
        'localmonth1',
        'localmonthname',
        'localmonthnamegen',
        'localmonthabbrev',
        'localday',
        'localday2',
        'localdayname',
        'localyear',
        'localtime',
        'localhour',
        'numberofarticles',
        'numberoffiles',
        'numberofedits',
        'articlepath',
        'pageid',
        'sitename',
        'server',
        'servername',
        'scriptpath',
        'stylepath',
        'pagename',
        'pagenamee',
        'fullpagename',
        'fullpagenamee',
        'namespace',
        'namespacee',
        'namespacenumber',
        'currentweek',
        'currentdow',
        'localweek',
        'localdow',
        'revisionid',
        'revisionday',
        'revisionday2',
        'revisionmonth',
        'revisionmonth1',
        'revisionyear',
        'revisiontimestamp',
        'revisionuser',
        'revisionsize',
        'subpagename',
        'subpagenamee',
        'talkspace',
        'talkspacee',
        'subjectspace',
        'subjectspacee',
        'talkpagename',
        'talkpagenamee',
        'subjectpagename',
        'subjectpagenamee',
        'numberofusers',
        'numberofactiveusers',
        'numberofpages',
        'currentversion',
        'rootpagename',
        'rootpagenamee',
        'basepagename',
        'basepagenamee',
        'currenttimestamp',
        'localtimestamp',
        'directionmark',
        'contentlanguage',
        'numberofadmins',
        'cascadingsources',
    ]

    switches = (
        '__NOTOC__',
        '__FORCETOC__',
        '__TOC__',
        '__NEWSECTIONLINK__',
        '__NONEWSECTIONLINK__',
        '__NOGALLERY__',
        '__HIDDENCAT__',
        '__NOCONTENTCONVERT__',
        '__NOCC__',
        '__NOTITLECONVERT__',
        '__NOTC__',
        '__START__',
        '__END__',
        '__INDEX__',
        '__NOINDEX__',
        '__STATICREDIRECT__',
        '__DISAMBIG__'
    )

    def __init__(self):
        """Initialize magic words with default values."""
        self.values = {'!': '|'}

    def __getitem__(self, name):
        """Get magic word value."""
        return self.values.get(name)

    def __setitem__(self, name, value):
        """Set magic word value."""
        self.values[name] = value

    def get(self, name, default=None):
        """Get magic word value with default."""
        return self.values.get(name, default)

    def update(self, values_dict):
        """Update multiple magic word values."""
        self.values.update(values_dict)


# Compiled regex for magic word switches
MAGIC_WORDS_RE = re.compile('|'.join(MagicWords.switches))


def substitute_magic_words(text, magic_words):
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
    for name in MagicWords.names:
        value = magic_words.get(name)
        if value is not None:
            # Simple substitution - in reality this would be more complex
            text = text.replace('{{' + name + '}}', str(value))
    
    return text


def remove_magic_word_switches(text):
    """
    Remove magic word behavioral switches from text.
    
    Args:
        text: Text containing magic word switches
        
    Returns:
        Text with switches removed
    """
    return MAGIC_WORDS_RE.sub('', text)
