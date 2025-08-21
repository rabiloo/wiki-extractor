"""
Template parsing and substitution engine for WikiExtractor
Handles MediaWiki template processing
"""

import logging
import re

MAX_PARAMETER_RECURSION_LEVELS = 16


def find_matching_braces(text, num_braces):
    """
    Find matching braces in text.

    Args:
        text: Text to search
        num_braces: Number of braces to match (2 for {{, 3 for {{{)

    Returns:
        List of (start, end) positions of matching braces
    """
    open_delim = '{' * num_braces
    close_delim = '}' * num_braces

    spans = []
    stack = []

    i = 0
    while i < len(text):
        if text[i:].startswith(open_delim):
            stack.append(i)
            i += num_braces
        elif text[i:].startswith(close_delim):
            if stack:
                start = stack.pop()
                spans.append((start, i + num_braces))
            i += num_braces
        else:
            i += 1

    return spans


def split_parts(text):
    """
    Split template or function parameters by pipes, respecting nested structures.

    Args:
        text: Text to split

    Returns:
        List of parameter parts
    """
    parts = []
    current = ''
    depth = 0

    i = 0
    while i < len(text):
        char = text[i]

        if char == '{':
            if i + 1 < len(text) and text[i + 1] == '{':
                depth += 1
                current += '{{'
                i += 2
                continue
        elif char == '}':
            if i + 1 < len(text) and text[i + 1] == '}':
                depth -= 1
                current += '}}'
                i += 2
                continue
        elif char == '[':
            if i + 1 < len(text) and text[i + 1] == '[':
                depth += 1
                current += '[['
                i += 2
                continue
        elif char == ']':
            if i + 1 < len(text) and text[i + 1] == ']':
                depth -= 1
                current += ']]'
                i += 2
                continue
        elif char == '|' and depth == 0:
            parts.append(current)
            current = ''
            i += 1
            continue

        current += char
        i += 1

    if current:
        parts.append(current)

    return parts


class Template(list):
    """
    A Template is a list of TemplateText or TemplateArgs
    """

    @classmethod
    def parse(cls, body):
        """
        Parse template body into Template object.
        
        Args:
            body: Template body text
            
        Returns:
            Template object
        """
        tpl = Template()
        # Handle nesting, e.g.:
        # {{{1|{{PAGENAME}}}
        # {{{italics|{{{italic|}}}
        # {{#if:{{{{{#if:{{{nominee|}}}|nominee|candidate}}|}}}|

        start = 0
        for s, e in find_matching_braces(body, 3):
            tpl.append(TemplateText(body[start:s]))
            tpl.append(TemplateArg(body[s + 3:e - 3]))
            start = e
        tpl.append(TemplateText(body[start:]))  # leftover
        return tpl

    def subst(self, params, extractor, depth=0):
        """
        Substitute parameters in template.
        
        Args:
            params: Parameter dictionary
            extractor: Extractor instance
            depth: Recursion depth
            
        Returns:
            Substituted template text
        """
        # We perform parameter substitutions recursively.
        # We also limit the maximum number of iterations to avoid too long or
        # even endless loops (in case of malformed input).

        logging.debug('subst tpl (%d, %d) %s', len(extractor.frame), depth, self)

        if depth > MAX_PARAMETER_RECURSION_LEVELS:
            extractor.recursion_exceeded_3_errs += 1
            return ''

        return ''.join([tpl.subst(params, extractor, depth) for tpl in self])

    def __str__(self):
        """String representation of template."""
        return ''.join([str(x) for x in self if x is not None])


class TemplateText(str):
    """Fixed text of template"""

    def subst(self, params, extractor, depth):
        """
        Substitute parameters (no-op for fixed text).
        
        Args:
            params: Parameter dictionary
            extractor: Extractor instance
            depth: Recursion depth
            
        Returns:
            The text itself (unchanged)
        """
        return self


class TemplateArg:
    """
    Parameter to a template.
    Has a name and a default value, both of which are Templates.
    """

    def __init__(self, parameter):
        """
        Initialize template argument.
        
        Args:
            parameter: The parts of a template argument
        """
        # The parameter name itself might contain templates, e.g.:
        #   appointe{{#if:{{{appointer14|}}}|r|d}}14|
        #   4|{{{{{subst|}}}CURRENTYEAR}}

        # Any parts in a template argument after the first (the parameter default) are
        # ignored, and an equals sign in the first part is treated as plain text.

        parts = split_parts(parameter)
        self.name = Template.parse(parts[0])
        if len(parts) > 1:
            # This parameter has a default value
            self.default = Template.parse(parts[1])
        else:
            self.default = None

    def __str__(self):
        """String representation of template argument."""
        if self.default:
            return '{{{%s|%s}}}' % (self.name, self.default)
        else:
            return '{{{%s}}}' % self.name

    def subst(self, params, extractor, depth):
        """
        Substitute value for this argument from parameter dictionary.
        
        Args:
            params: Parameter dictionary
            extractor: Extractor instance for evaluation
            depth: Recursion depth limit
            
        Returns:
            Substituted value
        """
        # The parameter name itself might contain templates, e.g.:
        # appointe{{#if:{{{appointer14|}}}|r|d}}14|
        param_name = self.name.subst(params, extractor, depth + 1)
        param_name = extractor.expandTemplates(param_name)

        result = ''
        if param_name in params:
            result = params[param_name]  # use parameter value specified in template invocation
        elif self.default:  # use the default value
            default_value = self.default.subst(params, extractor, depth + 1)
            result = extractor.expandTemplates(default_value)
            if result is None:
                return ''

        return result


def parse_template_parameters(parameters):
    """
    Build a dictionary with positional or named keys to expanded parameters.
    
    Args:
        parameters: The parts[1:] of a template, i.e. all except the title
        
    Returns:
        Dictionary of template parameters
    """
    template_params = {}

    if not parameters:
        return template_params

    # Parameters can be either named or unnamed. In the latter case, their
    # name is defined by their ordinal position (1, 2, 3, ...).

    unnamed_parameter_counter = 0

    # It's legal for unnamed parameters to be skipped, in which case they
    # will get default values (if available) during actual instantiation.
    # That is {{template_name|a||c}} means parameter 1 gets
    # the value 'a', parameter 2 value is not defined, and parameter 3 gets
    # the value 'c'. This case is correctly handled by function 'split',
    # and does not require any special handling.

    for param in parameters:
        # Spaces before or after a parameter value are normally ignored,
        # UNLESS the parameter contains a link (to prevent possible gluing
        # the link to the following text after template substitution)

        # Parameter values may contain "=" symbols, hence the parameter
        # name extends up to the first such symbol.

        # It is legal for a parameter to be specified several times, in
        # which case the last assignment takes precedence. Example:
        # "{{t|a|b|c|2=B}}" is equivalent to "{{t|a|B|c}}".
        # Therefore, we don't check if the parameter has been assigned a
        # value before, because anyway the last assignment should override
        # any previous ones.

        try:
            m = re.match(r" *([^=']*?) *=(.*)", param, re.DOTALL)
        except TypeError:
            continue

        if m:
            # This is a named parameter. This case also handles parameter
            # assignments like "2=xxx", where the number of an unnamed
            # parameter ("2") is specified explicitly - this is handled
            # transparently.

            parameter_name = m.group(1).strip()
            parameter_value = m.group(2)

            if ']]' not in parameter_value:  # if the value does not contain a link, trim whitespace
                parameter_value = parameter_value.strip()
            template_params[parameter_name] = parameter_value
        else:
            # This is an unnamed parameter
            unnamed_parameter_counter += 1

            if ']]' not in param:  # if the value does not contain a link, trim whitespace
                param = param.strip()
            template_params[str(unnamed_parameter_counter)] = param

    logging.debug('   templateParams> %s', '|'.join(template_params.values()))
    return template_params
