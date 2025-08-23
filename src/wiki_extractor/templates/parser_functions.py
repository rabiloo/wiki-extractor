import re
from typing import Any
from urllib.parse import quote as urlencode


def ucfirst(string: str) -> str:
    """Capitalize the first character of a string."""
    if string:
        return string[0].upper() + string[1:] if len(string) > 1 else string.upper()
    return ""


def lcfirst(string: str) -> str:
    """Lowercase the first character of a string."""
    if string:
        return string[0].lower() + string[1:] if len(string) > 1 else string.lower()
    return ""


def normalize_namespace(ns: str) -> str:
    """Normalize a namespace by capitalizing the first character."""
    return ucfirst(ns)


def fully_qualified_template_title(template_title: str, template_prefix: str = "") -> str:
    """Determine the namespace of a template title."""
    if template_title.startswith(":"):
        return ucfirst(template_title[1:])
    match = re.match(r"([^:]*)(:.*)", template_title)
    if match:
        prefix = normalize_namespace(match.group(1))
        if prefix in {"Template"}:
            return f"{prefix}{ucfirst(match.group(2))}"
    return f"{template_prefix}{ucfirst(template_title)}" if template_title else ""


def sharp_expr(expr: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        expr = re.sub(r"=", "==", expr)
        expr = re.sub(r"mod", "%", expr)
        expr = re.sub(r"\bdiv\b", "/", expr)
        expr = re.sub(r"\bround\b", "|ROUND|", expr)
        return str(eval(expr))
    except Exception:
        return '<span class="error"></span>'


def sharp_if(test_value: str, value_if_true: str, value_if_false: str = "", *args: Any) -> str:
    """Implement #if parser function."""
    if test_value.strip():
        value_if_true = value_if_true.strip()
        if value_if_true:
            return value_if_true
    elif value_if_false:
        return value_if_false.strip()
    return ""


def sharp_ifeq(lvalue: str, rvalue: str, value_if_true: str, value_if_false: str = "", *args: Any) -> str:
    """Implement #ifeq parser function."""
    rvalue = rvalue.strip()
    if rvalue and lvalue.strip() == rvalue:
        if value_if_true:
            return value_if_true.strip()
    elif value_if_false:
        return value_if_false.strip()
    return ""


def sharp_iferror(test: str, then: str = "", else_val: str = "", *args: Any) -> str:
    """Implement #iferror parser function."""
    if re.match(r'<(?:strong|span|p|div)\s(?:[^\s>]*\s+)*?class="(?:[^"\s>]*\s+)*?error(?:\s[^">]*)?"', test):
        return then
    return test.strip() if not else_val else else_val.strip()


def sharp_switch(primary: str, *params: str) -> str:
    """Implement #switch parser function."""
    primary = primary.strip()
    found = False
    default: str = ""
    rvalue: str = ""
    lvalue: str = ""
    for param in params:
        pair: list[str] = param.split("=", 1)
        lvalue = pair[0].strip()
        rvalue = pair[1].strip() if len(pair) > 1 else ""
        if found or primary in [v.strip() for v in lvalue.split("|")]:
            return rvalue
        if lvalue == "#default":
            default = rvalue
        rvalue = ""
    return lvalue if rvalue else default or ""


# def sharp_invoke(module: str, function: str, frame: list) -> str:
#     """Implement #invoke parser function."""
#     functions = modules.get(module, {})
#     funct = functions.get(function)
#     if funct:
#         template_title = fully_qualified_template_title(function)
#         pair = next((x for x in frame if x[0] == template_title), None)
#         if pair:
#             params = [pair[1].get(str(i + 1)) for i in range(len(pair[1]))]
#             return funct(*params)
#         return funct()
#     return ""


def call_parser_function(function_name: str, args: list[Any], frame: list[Any]) -> str:
    """Call a parser function with the given arguments."""
    parser_functions: dict[str, Any] = {
        "#expr": sharp_expr,
        "#if": sharp_if,
        "#ifeq": sharp_ifeq,
        "#iferror": sharp_iferror,
        "#ifexpr": lambda *args: "",
        "#ifexist": lambda *args: "",
        "#rel2abs": lambda *args: "",
        "#switch": sharp_switch,
        "#language": lambda *args: "",
        "#time": lambda *args: "",
        "#timel": lambda *args: "",
        "#titleparts": lambda *args: "",
        "urlencode": lambda string, *rest: urlencode(string),
        "lc": lambda string, *rest: string.lower() if string else "",
        "lcfirst": lambda string, *rest: lcfirst(string),
        "uc": lambda string, *rest: string.upper() if string else "",
        "ucfirst": lambda string, *rest: ucfirst(string),
        "int": lambda string, *rest: str(int(string)),
        "padleft": lambda char, width, string: string.ljust(char, int(width)),
    }
    try:
        # if function_name == '#invoke':
        #     return sharp_invoke(args[0].strip(), args[1].strip(), frame)
        if function_name in parser_functions:
            return parser_functions[function_name](*args)
    except Exception:
        return ""
    return ""
