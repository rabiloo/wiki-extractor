"""
Template processing logic for WikiExtractor
Handles template expansion and processing
"""

import logging
import re
import time

import babel
from bs4 import BeautifulSoup

from .magic_words import MagicWords
from .parser_functions import call_parser_function, fully_qualified_template_title
from .template_engine import Template, find_matching_braces, parse_template_parameters, split_parts

# Templates not to expand (regex patterns)
NOT_EXPAND_TEMPLATES_PATTERNS = [
    """'""",  # Triple quotes from original
    r"^\s+$",  # White spaces
    "!",
    "ISBN",
    "notelist",
    "rp",
    "MF",
    "Pie chart",
    "Graph",
    r"(.*)Infobox(.*)",  # Too complicated to parse
    r"(.*)Infotable(.*)",
    r"(.*)Image(.*)",
    "Flag",
    "pdf",
    "increase",
    "decrease",
    "color",
]

# Compile regex for not expand templates
NOT_EXPAND_TEMPLATES_RE = re.compile("|".join(NOT_EXPAND_TEMPLATES_PATTERNS), re.IGNORECASE)
# Template recursion limits
MAX_TEMPLATE_RECURSION_LEVELS = 30

SUBST_WORDS = "subst:|safesubst:"
AUX_TEMPLATE_COORD_AUX_VAR = ["""º""", """'""", """''"""]


def balance_brackets(string):
    """Balance curly brackets in a string."""
    if string is None:
        return None

    # Initialize stack to keep track of opening and closing brackets
    stack = []

    # Iterate over each character in the input string
    for c in string:
        if c == "{":
            stack.append(c)
        elif c == "}":
            # If there's a matching opening bracket, remove it
            if len(stack) > 0 and stack[-1] == "{":
                stack.pop()
            else:
                stack.append(c)

    # Balance the string by adding missing brackets
    return "{" * stack.count("}") + string + "}" * stack.count("{")


class TemplateProcessor:
    def __init__(self, title: str, ignore_templates: set = {}, discard_templates: set = {}):
        """
        Initialize template processor.
        """
        self.frame = []
        self.redirects = {}
        self.templates = {}
        self.template_cache = {}
        self.ignore_templates = ignore_templates
        self.discard_templates = discard_templates
        self.magic_words = MagicWords()
        self.recursion_exceeded_1_errs = 0  # template recursion within expandTemplates()
        self.recursion_exceeded_2_errs = 0  # template recursion within expandTemplate()
        self.recursion_exceeded_3_errs = 0  # parameter recursion
        self.template_title_errs = 0
        self._setup_magic_words(title)

    def _setup_magic_words(self, title: str):
        """Set up magic words for the current article."""
        self.magic_words["namespace"] = title[: max(0, title.find(":"))]
        self.magic_words["pagename"] = title
        self.magic_words["fullpagename"] = title
        self.magic_words["currentyear"] = time.strftime("%Y")
        self.magic_words["currentmonth"] = time.strftime("%m")
        self.magic_words["currentday"] = time.strftime("%d")
        self.magic_words["currenthour"] = time.strftime("%H")
        self.magic_words["currenttime"] = time.strftime("%H:%M:%S")

    def expand_template(self, body, language=None):
        """
        Expand template invocation.

        Args:
            body: The parts of a template
            language: Language code

        Returns:
            Expanded template content or None if template should be discarded
        """
        if len(self.frame) >= MAX_TEMPLATE_RECURSION_LEVELS:
            self.recursion_exceeded_2_errs += 1
            return ""

        logging.debug("INVOCATION %d %s", len(self.frame), body)

        parts = split_parts(body)
        title = self.expand_templates(parts[0].strip())

        if title is None:
            # Title included in config/discard_templates.txt
            return None
        elif re.match(NOT_EXPAND_TEMPLATES_RE, title):
            # Don't expand certain templates
            return ""
        elif title.lower() in self.ignore_templates:
            # Not expanding manually specified templates
            return ""
        elif title.lower() in self.discard_templates:
            # This whole doc is gonna be discarded
            return None

        # Handle language templates
        elif re.match("lang\-+", title, re.IGNORECASE):
            if language:
                try:
                    iso_code = parts[0].split("-")[1]
                    transl_lang_name = babel.Locale.parse(iso_code).get_display_name(language)
                    final_parse = transl_lang_name + ":" + str(parts[1])
                    return final_parse
                except babel.core.UnknownLocaleError:
                    # Some locale langauages might not work. E.g. "grc" or "an"
                    if len(parts) >= 2:
                        logging.debug("Lang. Template not found: " + str(parts[1]))
                        return str(parts[1])
                    else:
                        logging.debug("Lang. Template not found and not language detected in template name: " + title)
                        return ""
                except Exception:
                    if len(parts) >= 2:
                        return str(parts[1])
                    else:
                        return ""

            else:  # (This should never be the case), but code shuold not break...
                return ""

        elif re.match("lang", title, re.IGNORECASE):
            if len(parts) < 3:  # xml format error
                # raise Exception('LANG not well formated parts is bad:' + str(parts))
                return ""
            else:
                return str(parts[2])
        elif re.match("IPA", title, re.IGNORECASE):  # IPA  templates
            if len(parts) < 2:
                # xml format error
                return ""
            else:
                return str(parts[1])
            # elif(re.match('notelist',title,re.IGNORECASE) ):
            #    # problems with list and inner references
            #    return ''
        elif re.match("segle", title, re.IGNORECASE):
            if len(parts) < 2:
                return ""
            else:
                segle_tpl = "{{uc:" + str(parts[1]) + "}}"
                segle = self.expand_templates(segle_tpl)
                if segle is None:
                    return None

            if len(parts) == 2:
                return "segle " + str(segle)

            elif len(parts) >= 3:
                if parts[2] == "-":
                    return "segle " + str(segle) + " aC"
                else:
                    return "segle " + str(segle)
            else:
                return ""
        elif re.match("coord", title, re.IGNORECASE):
            if len(parts) == 3:
                return parts[1] + "ºN, " + parts[2] + " ºW"

            else:
                coord_1 = []
                coord_2 = []
                coord_1_dir = ""
                coord_2_dir = ""
                coord_1_completed = False

                for e in parts[1:]:
                    if re.match("N", e, re.IGNORECASE) or re.match("S", e, re.IGNORECASE):
                        coord_1_dir = e
                        coord_1_completed = True
                    elif not coord_1_completed:
                        coord_1.append(e)
                    elif re.match("W", e, re.IGNORECASE) or re.match("E", e, re.IGNORECASE):
                        coord_2_dir = e
                        break
                    elif not re.match(r"\w*(=|:)\w*", e, re.IGNORECASE):  # other args
                        coord_2.append(e)
                    else:
                        break

                final_coord_1 = ""
                final_coord_2 = ""
                if any(coord_1) and len(coord_1) == len(coord_2):
                    for i, e in enumerate(coord_1):
                        if i > (len(AUX_TEMPLATE_COORD_AUX_VAR) - 1):
                            break
                        final_coord_1 += str(coord_1[i]) + AUX_TEMPLATE_COORD_AUX_VAR[i]
                        final_coord_2 += str(coord_2[i]) + AUX_TEMPLATE_COORD_AUX_VAR[i]
                    final_coord_1 += coord_1_dir
                    final_coord_2 += coord_2_dir
                    return final_coord_1 + ", " + final_coord_2
                else:
                    return ""

        elif re.match("audio", title, re.IGNORECASE):
            if len(parts) == 3:
                return parts[2]
            else:
                return ""

        # SUBST
        # Apply the template tag to parameters without
        # substituting into them, e.g.
        # {{subst:t|a{{{p|q}}}b}} gives the wikitext start-a{{{p|q}}}b-end
        # @see https://www.mediawiki.org/wiki/Manual:Substitution#Partial_substitution
        subst = False
        if re.match(SUBST_WORDS, title, re.IGNORECASE):
            title = re.sub(SUBST_WORDS, "", title, 1, re.IGNORECASE)
            subst = True

        if title.lower() in self.magic_words.values:
            return self.magic_words[title.lower()]

        # Parser functions
        # The first argument is everything after the first colon.
        # It has been evaluated above.
        colon = title.find(":")
        if colon > 1:
            funct = title[:colon]
            parts[0] = title[colon + 1 :].strip()  # side-effect (parts[0] not used later)
            # arguments after first are not evaluated
            # ret = callParserFunction(funct, parts, self.frame)
            # return self.expandTemplates(ret)

            ret = call_parser_function(funct, parts, self.frame)
            call_result = self.expand_templates(ret)
            if call_result is None:
                return ""
            else:
                return call_result
            # return

        title = fully_qualified_template_title(title)
        if not title:
            self.template_title_errs += 1
            return ""

        redirected = self.redirects.get(title)
        if redirected:
            title = redirected

        # get the template
        if title in self.template_cache:
            template = self.template_cache[title]
        elif title in self.templates:
            template = Template.parse(self.templates[title])
            # add it to cache
            self.template_cache[title] = template
            del self.templates[title]
        else:
            # The page being included could not be identified
            return ""

        # logging.debug('TEMPLATE %s: %s', title, template)

        # tplarg          = "{{{" parts "}}}"
        # parts           = [ title *( "|" part ) ]
        # part            = ( part-name "=" part-value ) / ( part-value )
        # part-name       = wikitext-L3
        # part-value      = wikitext-L3
        # wikitext-L3     = literal / template / tplarg / link / comment /
        #                   line-eating-comment / unclosed-comment /
        #           	    xmlish-element / *wikitext-L3

        # A tplarg may contain other parameters as well as templates, e.g.:
        #   {{{text|{{{quote|{{{1|{{error|Error: No text given}}}}}}}}}}}
        # hence no simple RE like this would work:
        #   '{{{((?:(?!{{{).)*?)}}}'
        # We must use full CF parsing.

        # the parameter name itself might be computed, e.g.:
        #   {{{appointe{{#if:{{{appointer14|}}}|r|d}}14|}}}

        # Because of the multiple uses of double-brace and triple-brace
        # syntax, expressions can sometimes be ambiguous.
        # Precedence rules specifed here:
        # http://www.mediawiki.org/wiki/Preprocessor_ABNF#Ideal_precedence
        # resolve ambiguities like this:
        #   {{{{ }}}} -> { {{{ }}} }
        #   {{{{{ }}}}} -> {{ {{{ }}} }}
        #
        # :see: https://en.wikipedia.org/wiki/Help:Template#Handling_parameters

        params = parts[1:]

        if not subst:
            # Evaluate parameters, since they may contain templates, including
            # the symbol "=".
            # {{#ifexpr: {{{1}}} = 1 }}
            params = [self.expand_templates(p) for p in params if p is not None]

        # build a dict of name-values for the parameter values
        params = self.template_params(params)

        # Perform parameter substitution
        # extend frame before subst, since there may be recursion in default
        # parameter value, e.g. {{OTRS|celebrative|date=April 2015}} in article
        # 21637542 in enwiki.
        self.frame.append((title, params))
        instantiated = template.subst(params, self)

        # logging.debug('instantiated %d %s', len(self.frame), instantiated)

        # Sometimes this generates html code with templates inside
        try:
            instantiated_html_clean = BeautifulSoup(instantiated, "html.parser").get_text()
        except Exception as e:
            instantiated_html_clean = instantiated

        value = self.expand_templates(instantiated_html_clean)
        if value is None:
            # self.frame.pop()
            return ""
        # value = self.expandTemplates(instantiated)

        # sometimes value has unbalances brackets
        value = balance_brackets(value)

        self.frame.pop()
        # logging.debug('   INVOCATION> %s %d %s', title, len(self.frame), value)
        return value

    def expand_templates(self, wikitext, language=None):
        """
        Expand templates in wikitext.

        Args:
            wikitext: The text to be expanded
            language: Language code

        Returns:
            Text with templates expanded, or None if expansion failed
        """
        # Templates are frequently nested. Occasionally, parsing mistakes may
        # cause template insertion to enter an infinite loop, for instance when
        # trying to instantiate Template:Country
        #
        # {{country_{{{1}}}|{{{2}}}|{{{2}}}|size={{{size|}}}|name={{{name|}}}}}
        #
        # which is repeatedly trying to insert template 'country_', which is
        # again resolved to Template:Country. The straightforward solution of
        # keeping track of templates that were already inserted for the current
        # article would not work, because the same template may legally be used
        # more than once, with different parameters in different parts of the
        # article. Therefore, we limit the number of iterations of nested
        # template inclusion.

        result = ""
        if len(self.frame) >= MAX_TEMPLATE_RECURSION_LEVELS:
            self.recursion_exceeded_1_errs += 1
            return None

        cur = 0
        # Look for matching {{...}}
        for s, e in find_matching_braces(wikitext, 2):
            content = self.expand_template(wikitext[s + 2 : e - 2], language)
            if content is None:
                # This happens when a template specified in
                # config/discard_templates.txt appears. The whole doc will be discarded.
                return None
            else:
                result += wikitext[cur:s] + content
                cur = e

        # Add leftover text
        result += wikitext[cur:]
        return result

    def template_params(self, parameters):
        """
        Build a dictionary with positional or name key to expanded parameters.

        Args:
            parameters: The parts[1:] of a template, i.e. all except the title

        Returns:
            Dictionary of template parameters
        """
        return parse_template_parameters(parameters)
