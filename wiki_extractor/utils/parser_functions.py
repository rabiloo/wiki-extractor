import re

from .utils import ucfirst, lcfirst, fully_qualified_template_title
from urllib.parse import quote as urlencode

class Infix:
    """Infix operator for parser functions."""

    def __init__(self, function):
        self.function = function

    def __ror__(self, other):
        return Infix(lambda x, self, other: self.function(other, x))

    def __or__(self, other):
        return self.function(other)

    def __rlshift__(self, other):
        return Infix(lambda x, self, other: self.function(other, x))

    def __rshift__(self, other):
        return self.function(other)

    def __call__(self, value1, value2):
        return self.function(value1, value2)

ROUND = Infix(lambda x, y: round(x, y))

def sharp_expr(expr: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        expr = re.sub(r'=', '==', expr)
        expr = re.sub(r'mod', '%', expr)
        expr = re.sub(r'\bdiv\b', '/', expr)
        expr = re.sub(r'\bround\b', '|ROUND|', expr)
        return str(eval(expr))
    except:
        return '<span class="error"></span>'

def sharp_if(test_value: str, value_if_true: str, value_if_false: str = None, *args) -> str:
    """Implement #if parser function."""
    if test_value.strip():
        value_if_true = value_if_true.strip()
        if value_if_true:
            return value_if_true
    elif value_if_false:
        return value_if_false.strip()
    return ""

def sharp_ifeq(lvalue: str, rvalue: str, value_if_true: str, value_if_false: str = None, *args) -> str:
    """Implement #ifeq parser function."""
    rvalue = rvalue.strip()
    if rvalue and lvalue.strip() == rvalue:
        if value_if_true:
            return value_if_true.strip()
    elif value_if_false:
        return value_if_false.strip()
    return ""

def sharp_iferror(test: str, then: str = '', else_val: str = None, *args) -> str:
    """Implement #iferror parser function."""
    if re.match(r'<(?:strong|span|p|div)\s(?:[^\s>]*\s+)*?class="(?:[^"\s>]*\s+)*?error(?:\s[^">]*)?"', test):
        return then
    return test.strip() if else_val is None else else_val.strip()

def sharp_switch(primary: str, *params) -> str:
    """Implement #switch parser function."""
    primary = primary.strip()
    found = False
    default = None
    rvalue = None
    lvalue = ''
    for param in params:
        pair = param.split('=', 1)
        lvalue = pair[0].strip()
        rvalue = pair[1].strip() if len(pair) > 1 else None
        if found or primary in [v.strip() for v in lvalue.split('|')]:
            return rvalue
        if lvalue == '#default':
            default = rvalue
        rvalue = None
    return lvalue if rvalue is not None else default or ''

def sharp_invoke(module: str, function: str, frame: list) -> str:
    """Implement #invoke parser function."""
    functions = modules.get(module, {})
    funct = functions.get(function)
    if funct:
        template_title = fully_qualified_template_title(function)
        pair = next((x for x in frame if x[0] == template_title), None)
        if pair:
            params = [pair[1].get(str(i + 1)) for i in range(len(pair[1]))]
            return funct(*params)
        return funct()
    return ""

def call_parser_function(function_name: str, args: list, frame: list) -> str:
    """Call a parser function with the given arguments."""
    parser_functions = {
        '#expr': sharp_expr,
        '#if': sharp_if,
        '#ifeq': sharp_ifeq,
        '#iferror': sharp_iferror,
        '#ifexpr': lambda *args: '',
        '#ifexist': lambda *args: '',
        '#rel2abs': lambda *args: '',
        '#switch': sharp_switch,
        '#language': lambda *args: '',
        '#time': lambda *args: '',
        '#timel': lambda *args: '',
        '#titleparts': lambda *args: '',
        'urlencode': lambda string, *rest: urlencode(string),
        'lc': lambda string, *rest: string.lower() if string else '',
        'lcfirst': lambda string, *rest: lcfirst(string),
        'uc': lambda string, *rest: string.upper() if string else '',
        'ucfirst': lambda string, *rest: ucfirst(string),
        'int': lambda string, *rest: str(int(string)),
        'padleft': lambda char, width, string: string.ljust(char, int(width)),
    }
    try:
        if function_name == '#invoke':
            return sharp_invoke(args[0].strip(), args[1].strip(), frame)
        if function_name in parser_functions:
            return parser_functions[function_name](*args)
    except:
        return ""
    return ""

modules = {}  # Placeholder for extension modules