"""
Math formula processing for WikiExtractor
Handles conversion of LaTeX math expressions to readable text
"""

import re
from ..utils.regex_patterns import MATH_COMPILED_PATTERNS

def process_math_content(match):
    latex_content = match.group(1).strip()

    if not re.search(r'[\\{}^_$|∑∏∫≤≥≠∞α-ωΑ-Ω]|frac|sum|prod|int|sqrt|begin|end', latex_content):
        return f' {latex_content} '

    is_display = bool(re.search(r'display\s*=\s*["\']?block["\']?', match.group(0), re.IGNORECASE))

    cleaned = clean_latex_content(latex_content)

    if is_display:
        return f'\n\n$$ {cleaned} $$\n\n'
    else:
        return f' $ {cleaned} $ '

def clean_latex_content(latex_content):
    cleaned = latex_content
    if not re.search(r'\\begin\{(align|cases|array|matrix)', cleaned):
        cleaned = re.sub(r'\s*&\s*', ' ', cleaned)

        # Clean up spacing and line breaks
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\\\\+', r'\\\\', cleaned)

    # Add spaces around operators
    cleaned = re.sub(r'([=<>≤≥≠±∓])', r' \1 ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Clean up double spaces

    # Replace common LaTeX symbols with Unicode equivalents
    cleaned = apply_latex_symbol_replacements(cleaned)

    return cleaned.strip()

def apply_latex_symbol_replacements(text):
    replacements = {
        r'\\infty\b': '∞',
        r'\\sum\b': '∑',
        r'\\prod\b': '∏',
        r'\\int\b': '∫',
        r'\\leq\b': '≤',
        r'\\geq\b': '≥',
        r'\\neq\b': '≠',
        r'\\approx\b': '≈',
        r'\\alpha\b': 'α',
        r'\\beta\b': 'β',
        r'\\gamma\b': 'γ',
        r'\\delta\b': 'δ',
        r'\\epsilon\b': 'ε',
        r'\\theta\b': 'θ',
        r'\\lambda\b': 'λ',
        r'\\mu\b': 'μ',
        r'\\pi\b': 'π',
        r'\\sigma\b': 'σ',
        r'\\phi\b': 'φ',
        r'\\omega\b': 'ω',
        r'\\Omega\b': 'Ω',
        r'\\Delta\b': 'Δ',
        r'\\Gamma\b': 'Γ',
        r'\\Theta\b': 'Θ'
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text

def process_text_with_math(text):
    for pattern in MATH_COMPILED_PATTERNS:
        text = pattern.sub(process_math_content, text)

    return text