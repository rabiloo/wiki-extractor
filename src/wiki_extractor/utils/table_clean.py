import re


def clean_cell(cell: str) -> str:
    """Clean cell content by removing basic wiki markup."""
    # Remove HTML tags
    cell = re.sub(r"<[^>]*>", "", cell)

    # Convert wiki links [[link|text]] -> text or [[link]] -> link
    cell = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", cell)
    cell = re.sub(r"\[\[([^\]]+)\]\]", r"\1", cell)

    # Convert wiki formatting
    cell = re.sub(r"'''([^']+)'''", r"**\1**", cell)  # bold
    cell = re.sub(r"''([^']+)''", r"*\1*", cell)  # italic

    # Remove references
    cell = re.sub(r"<ref[^>]*>.*?</ref>", "", cell)
    cell = re.sub(r"<ref[^>]*>", "", cell)

    # Clean whitespace and escape pipes
    cell = re.sub(r"\s+", " ", cell).strip()
    cell = cell.replace("|", "&#124;")

    return cell if cell else " "


def remove_attributes(text: str) -> str:
    """Remove HTML attributes from text, keeping only content."""
    # Remove common attributes patterns
    text = re.sub(r"\s*colspan=\d+", "", text)
    text = re.sub(r"\s*rowspan=\d+", "", text)
    text = re.sub(r'\s*style="[^"]*"', "", text)
    text = re.sub(r'\s*class="[^"]*"', "", text)
    text = re.sub(r"\s*align=\w+", "", text)
    text = re.sub(r'\s*width="[^"]*"', "", text)
    text = re.sub(r'\s*height="[^"]*"', "", text)
    text = re.sub(r'\s*bgcolor="[^"]*"', "", text)
    text = re.sub(r"\s*valign=\w+", "", text)

    return text.strip()


def parse_row_cells(line: str) -> list:
    """Parse table row and return list of cells."""
    # Remove leading marker (| or !)
    if line.startswith(("|", "!")):
        line = line[1:]

    cells = []

    # Handle double separators first (!! or ||)
    if "!!" in line:
        cells = line.split("!!")
    elif "||" in line:
        cells = line.split("||")
    else:
        # Handle single | - need to separate attributes from content
        parts = line.split("|")
        cells = []

        for part in parts:
            # If part contains attributes (has = signs), extract content after last |
            if "=" in part and "|" not in part:
                # This is likely just attributes, skip it
                continue
            else:
                cells.append(part)

    # Clean and process each cell
    processed_cells = []
    for cell in cells:
        # Remove attributes from cell content
        cell = remove_attributes(cell)
        # Clean the cell content
        cleaned = clean_cell(cell)
        processed_cells.append(cleaned)

    return processed_cells


def convert_table_to_markdown(content: str) -> str:
    """Convert wiki table to markdown maintaining row/column structure."""
    lines = [line.strip() for line in content.split("\n") if line.strip()]

    rows = []
    caption = ""

    for line in lines:
        # Skip table boundaries and row separators
        if line.startswith(("{|", "|}", "|-")):
            continue

        # Handle caption
        if line.startswith("|+"):
            caption = clean_cell(line[2:])
            continue

        # Handle header row
        if line.startswith("!"):
            cells = parse_row_cells(line)
            if cells:
                rows.append(("header", cells))

        # Handle data row
        elif line.startswith("|"):
            cells = parse_row_cells(line)
            if cells:
                rows.append(("data", cells))

    # Build markdown table
    if not rows:
        return ""

    # Determine max column count to ensure consistent structure
    max_cols = max(len(row[1]) for row in rows)

    markdown_lines = []

    # Add caption if exists
    if caption:
        markdown_lines.append(f"**{caption}**")
        markdown_lines.append("")

    header_added = False

    for row_type, cells in rows:
        # Pad cells to max columns to maintain structure
        padded_cells = cells + [" "] * (max_cols - len(cells))

        # Create markdown row
        markdown_row = "| " + " | ".join(padded_cells) + " |"
        markdown_lines.append(markdown_row)

        # Add header separator after first header row
        if row_type == "header" and not header_added:
            separator = "|" + " --- |" * max_cols
            markdown_lines.append(separator)
            header_added = True
        # Add header separator before first data row if no header exists
        elif row_type == "data" and not header_added:
            # Insert empty header row
            empty_header = "| " + " | ".join([" "] * max_cols) + " |"
            separator = "|" + " --- |" * max_cols
            markdown_lines.insert(-1, empty_header)
            markdown_lines.insert(-1, separator)
            header_added = True

    return "\n".join(markdown_lines)
