import re
from typing import Dict

entities = {
    # Math operators
    "&minus;": "−",
    "&times;": "×",
    "&divide;": "÷",
    "&plusmn;": "±",
    "&le;": "≤",
    "&ge;": "≥",
    "&ne;": "≠",
    "&equiv;": "≡",
    "&approx;": "≈",
    "&infin;": "∞",
    "&sum;": "∑",
    "&prod;": "∏",
    "&int;": "∫",
    "&part;": "∂",
    "&radic;": "√",
    "&deg;": "°",
    "&micro;": "μ",
    "&prop;": "∝",
    # Greek letters
    "&alpha;": "α",
    "&beta;": "β",
    "&gamma;": "γ",
    "&delta;": "δ",
    "&theta;": "θ",
    "&lambda;": "λ",
    "&mu;": "μ",
    "&pi;": "π",
    "&sigma;": "σ",
    "&tau;": "τ",
    "&phi;": "φ",
    "&omega;": "ω",
    "&Delta;": "Δ",
    "&Gamma;": "Γ",
    "&Lambda;": "Λ",
    "&Omega;": "Ω",
    # Fractions & superscripts
    "&frac12;": "½",
    "&frac14;": "¼",
    "&frac34;": "¾",
    "&frac13;": "⅓",
    "&sup1;": "¹",
    "&sup2;": "²",
    "&sup3;": "³",
    "&sub1;": "₁",
    "&sub2;": "₂",
    "&sub3;": "₃",
    # Set theory & logic
    "&isin;": "∈",
    "&notin;": "∉",
    "&sub;": "⊂",
    "&cup;": "∪",
    "&cap;": "∩",
    "&empty;": "∅",
    "&exist;": "∃",
    "&forall;": "∀",
    "&rarr;": "→",
    "&larr;": "←",
    "&harr;": "↔",
    "&rArr;": "⇒",
    "&lArr;": "⇐",
}

# Common transformations for HTML/wiki templates
html_transforms = [
    (r"\{\{=\}\}", "="),  # Template equals
    (r"\{\{!\}\}", "|"),  # Template pipe
    (r"^1\s*=\s*", ""),  # Parameter prefix
    (r"'''([^']+)'''", r"**\1**"),  # Bold
    (r"''([^']+)''", r"*\1*"),  # Italic
    (r"<sup>([^<>]*)</sup>", r"^\1"),  # Superscript
    (r"<sub>([^<>]*)</sub>", r"_\1"),  # Subscript
    (r"<sup>(\d+)</sup>⁄<sub>(\d+)</sub>", r"\1/\2"),  # Fractions
    (r"<br\s*/?>", " "),  # Line breaks
    (r"<[^>]+>", ""),  # Remove HTML tags
    (r"\s*([()[\]{}])\s*", r"\1"),  # Brackets spacing
    (r"\s+", " "),  # Multiple spaces
]

# Operators for spacing
operators = ["=", "≠", "≈", "±", "×", "÷", "≤", "≥", "+", "-", "→", "←", "⇒", "⇐"]

# Special characters that need backtick wrapping
special_chars = "×÷±≤≥≠≈∞∑∏∫√αβγδθλμπσφωΔΓΛΩ∈∉⊂∪∩∅∃∀→←↔⇒⇐"


def parse_template_content(template_content: str) -> Dict[str, str]:
    """
    Parse template content to extract parameters.

    Args:
        template_content: Content inside the template (without {{ }})

    Returns:
        Dictionary with template name and parameters
    """
    parts = []
    current_part = ""
    brace_level = 0
    bracket_level = 0

    for char in template_content:
        if char == "{":
            brace_level += 1
        elif char == "}":
            brace_level -= 1
        elif char == "[":
            bracket_level += 1
        elif char == "]":
            bracket_level -= 1
        elif char == "|" and brace_level == 0 and bracket_level == 0:
            parts.append(current_part.strip())
            current_part = ""
            continue
        current_part += char

    if current_part:
        parts.append(current_part.strip())

    if not parts:
        return {}

    template_name = parts[0].lower().strip()
    params = {}

    for i, part in enumerate(parts[1:], 1):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
        else:
            params[str(i)] = part.strip()

    params["_template_name"] = template_name
    return params


def convert_cite_web_to_markdown(params: Dict[str, str]) -> str:
    """Convert {{cite web}} template to Markdown format."""
    title = params.get("title", "")
    url = params.get("url", "")
    author = params.get("author", params.get("last", ""))
    if author and params.get("first", ""):
        author = f"{params['first']} {author}"
    date = params.get("date", params.get("year", ""))
    website = params.get("website", params.get("work", ""))
    access_date = params.get("access-date", params.get("accessdate", ""))

    markdown = ""
    if title and url:
        markdown = f"[{title}]({url})"
    elif title:
        markdown = f"*{title}*"
    elif url:
        markdown = f"<{url}>"

    details = []
    if author:
        details.append(f"by {author}")
    if website:
        details.append(f"*{website}*")
    if date:
        details.append(date)
    if access_date:
        details.append(f"(accessed {access_date})")

    if details:
        markdown += ". " + ", ".join(details)
    if not markdown:
        markdown = "No title or URL provided."
    return markdown


def convert_cite_journal_to_markdown(params: Dict[str, str]) -> str:
    """Convert {{cite journal}} template to Markdown format."""
    title = params.get("title", "")
    journal = params.get("journal", "")
    author = params.get("author", params.get("last", ""))
    if author and params.get("first", ""):
        author = f"{params['first']} {author}"
    date = params.get("date", params.get("year", ""))
    volume = params.get("volume", "")
    issue = params.get("issue", "")
    pages = params.get("pages", params.get("page", ""))
    doi = params.get("doi", "")
    url = params.get("url", "")

    markdown = ""
    if author:
        markdown += f"{author}. "
    if title:
        if url:
            markdown += f'"[{title}]({url})". '
        else:
            markdown += f'"{title}". '
    if journal:
        markdown += f"*{journal}*"

    citation_details = []
    if volume:
        vol_text = f"vol. {volume}"
        if issue:
            vol_text += f", no. {issue}"
        citation_details.append(vol_text)
    if date:
        citation_details.append(date)
    if pages:
        citation_details.append(f"pp. {pages}")

    if citation_details:
        markdown += ", " + ", ".join(citation_details)

    if doi:
        markdown += f". DOI: {doi}"

    return markdown


def convert_cite_book_to_markdown(params: Dict[str, str]) -> str:
    """Convert {{cite book}} template to Markdown format."""
    title = params.get("title", "")
    author = params.get("author", params.get("last", ""))
    if author and params.get("first", ""):
        author = f"{params['first']} {author}"
    publisher = params.get("publisher", "")
    date = params.get("date", params.get("year", ""))
    isbn = params.get("isbn", "")
    url = params.get("url", "")
    chapter = params.get("chapter", "")
    pages = params.get("pages", params.get("page", ""))

    markdown = ""
    if author:
        markdown += f"{author}. "

    if chapter:
        if title:
            markdown += f'"{chapter}" in '

    if title:
        if url:
            markdown += f"*[{title}]({url})*"
        else:
            markdown += f"*{title}*"

    details = []
    if publisher:
        details.append(publisher)
    if date:
        details.append(date)
    if pages:
        details.append(f"pp. {pages}")
    if isbn:
        details.append(f"ISBN: {isbn}")

    if details:
        markdown += ". " + ", ".join(details)

    return markdown


def convert_image_to_markdown(params: Dict[str, str]) -> str:
    """Convert image templates to Markdown format."""
    # Extract image name from first parameter or 'file' parameter
    image_name = params.get("1", params.get("file", ""))
    caption = params.get("caption", params.get("2", ""))
    alt = params.get("alt", "")

    if not image_name:
        return ""

    # Clean up image name
    if image_name.lower().startswith(("file:", "image:")):
        image_name = image_name.split(":", 1)[1]

    # For Wikipedia images, construct the commons URL
    image_url = f"https://commons.wikimedia.org/wiki/File:{image_name.replace(' ', '_')}"

    if caption:
        return f"![{alt or caption}]({image_url})\n*{caption}*"
    else:
        return f"![{alt or 'Image'}]({image_url})"


def convert_math_latex_template_to_markdown(content: str) -> str:
    """Convert LaTeX templates (tmath, texmath) - preserve LaTeX syntax."""
    if not content:
        return ""

    # Minimal cleanup for LaTeX
    content = re.sub(r"\{\{=\}\}", "=", content)
    content = re.sub(r"\{\{!\}\}", "|", content)
    content = re.sub(r"^1\s*=\s*", "", content.strip())

    return f"${content}$"


def convert_math_html_template_to_markdown(content: str) -> str:
    """Convert HTML/wiki templates (math, mvar, var) to readable Markdown."""
    if not content:
        return ""

    # Apply transformations pipeline
    for pattern, replacement in html_transforms:
        content = re.sub(pattern, replacement, content.strip())

    # Replace HTML entities (including double-escaped)
    for entity, char in entities.items():
        content = content.replace(entity, char)
        content = content.replace(f"&amp;{entity[1:]}", char)

    # Add spacing around operators
    for op in operators:
        content = re.sub(rf"\s*{re.escape(op)}\s*", f" {op} ", content)

    # Final cleanup
    content = re.sub(r"\s+", " ", content.strip())
    content = re.sub(r"(\w+)\s*\(", r"\1(", content)  # Function calls

    # Wrap in backticks if contains special characters or formatting
    has_special = any(c in content for c in special_chars)
    has_formatting = any(c in content for c in "^_*")

    if has_special or has_formatting:
        return f"`{content}`"

    return content


def convert_template_to_markdown(template_name: str, params: Dict[str, str]) -> str:
    """Convert various templates to Markdown format."""
    template_name = template_name.lower().strip()

    # Citation templates
    if template_name in ["cite web", "citation", "cite website"]:
        return convert_cite_web_to_markdown(params)
    elif template_name in ["cite journal", "cite paper"]:
        return convert_cite_journal_to_markdown(params)
    elif template_name in ["cite book", "cite publication"]:
        return convert_cite_book_to_markdown(params)
    elif template_name in ["cite news", "cite newspaper"]:
        return convert_cite_journal_to_markdown(params)  # Similar format

    # Image templates
    elif template_name in ["file", "image", "img"]:
        return convert_image_to_markdown(params)

    # Quote templates
    elif template_name in ["quote", "blockquote", "cquote"]:
        quote_text = params.get("1", params.get("text", ""))
        author = params.get("author", params.get("2", ""))
        if quote_text:
            if author:
                return f"> {quote_text}\n> \n> — {author}"
            else:
                return f"> {quote_text}"

    # Conversion templates
    elif template_name in ["convert", "cvt"]:
        value = params.get("1", "")
        from_unit = params.get("2", "")
        to_unit = params.get("3", "")
        if value and from_unit:
            return f"{value} {from_unit}" + (f" ({to_unit})" if to_unit else "")

    # About templates
    elif template_name in ["about", "for", "other uses"]:
        text = params.get("1", "")
        return f"*This article is about {text}.*" if text else ""

    # Variables and data
    elif template_name in ["var", "variable"]:
        return params.get("1", "")

    # Math templates
    elif template_name in ["math", "mvar", "var", "tmath"]:
        math_content = params.get("1", params.get("content", ""))
        if template_name in ["tmath", "texmath", "latex"]:
            return convert_math_latex_template_to_markdown(math_content)

        elif template_name in ["math", "mvar", "var", "variable"]:
            return convert_math_html_template_to_markdown(math_content)

    # Default: return empty string for unhandled templates
    return ""
