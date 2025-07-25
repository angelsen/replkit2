#!/usr/bin/env python3
"""
README renderer - converts markdown to ASCII art using TextKit.

This demonstrates TextKit's display capabilities by rendering
a markdown file as pure ASCII with proper spacing and formatting.
"""

import re
from pathlib import Path
from replkit2.textkit import box, table, list_display, hr, compose, align, wrap, config

# Set page width for consistent formatting
config.width = 80


def parse_markdown(content: str) -> list[str]:
    """Parse markdown content into TextKit display elements."""
    sections = []
    lines = content.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Headers with level detection
        if match := re.match(r"^(#{1,3})\s+(.+)$", line):
            level = len(match.group(1))
            title = match.group(2)
            sections.append(render_header(title, level))
            i += 1

        # Horizontal rules
        elif line in ["---", "***", "___"]:
            sections.append(hr("="))
            i += 1

        # Code blocks
        elif line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if code_lines:
                sections.append(box("\n".join(code_lines), title="CODE"))
            i += 1

        # Tables
        elif "|" in line and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            headers = parse_table_row(line)
            i += 2  # Skip separator

            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append(parse_table_row(lines[i]))
                i += 1

            sections.append(table(rows, headers))

        # Lists (bullet points)
        elif re.match(r"^[*\-+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[*\-+]\s+", lines[i].strip()):
                items.append(lines[i].strip()[2:])
                i += 1
            sections.append(list_display(items, style="bullet"))

        # Numbered lists
        elif re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            sections.append(list_display(items, numbered=True))

        # Paragraphs
        else:
            para_lines = []
            while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
                para_lines.append(lines[i].strip())
                i += 1

            if para_lines:
                paragraph = process_inline_formatting(" ".join(para_lines))
                sections.extend(wrap(paragraph, config.width))

    return sections


def render_header(title: str, level: int) -> str:
    """Render a header with appropriate formatting."""
    if level == 1:
        # H1: uppercase in box with separator
        return compose(box(title.upper(), title="H1"), hr("-"), spacing=0)
    elif level == 2:
        # H2: normal case in box with separator
        return compose(box(title, title="H2"), hr("-"), spacing=0)
    else:
        # H3: normal case in box with separator
        return compose(box(title, title="H3"), hr("-"), spacing=0)


def parse_table_row(line: str) -> list[str]:
    """Parse a markdown table row."""
    return [cell.strip() for cell in line.split("|")[1:-1]]


def is_table_separator(line: str) -> bool:
    """Check if a line is a table separator."""
    return "|" in line and "-" in line


def is_block_start(line: str) -> bool:
    """Check if a line starts a new block element."""
    line = line.strip()
    return (
        line.startswith("#")
        or line.startswith("```")
        or line in ["---", "***", "___"]
        or "|" in line
        or re.match(r"^[*\-+]\s+", line) is not None
        or re.match(r"^\d+\.\s+", line) is not None
    )


def process_inline_formatting(text: str) -> str:
    """Process inline markdown formatting."""
    # Code spans
    text = re.sub(r"`([^`]+)`", r"[\1]", text)

    # Bold (both ** and __)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)

    # Italic (both * and _)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    return text


def create_header() -> str:
    """Create the document header."""
    return compose(
        hr("="),
        align("ReplKit2 - README", mode="center"),
        align("Rendered with TextKit", mode="center"),
        hr("="),
        spacing=1,
    )


def create_footer() -> str:
    """Create the document footer."""
    return compose(
        hr("="),
        align("Generated from examples/README.md", mode="center"),
        hr("="),
        spacing=1,
    )


def render_markdown(md_path: str) -> str:
    """Render a markdown file as ASCII art."""
    content = Path(md_path).read_text()

    # Remove trailing "Built with" section if present
    if "---" in content:
        parts = content.rsplit("---", 1)
        if len(parts) == 2 and "Built with" in parts[1] and "❤️" in parts[1]:
            content = parts[0].strip()

    # Parse markdown into sections
    sections = parse_markdown(content)

    # Compose the complete document
    return compose(
        create_header(),
        *sections,
        create_footer(),
        spacing=1,  # Auto-spacing between all major sections
    )


if __name__ == "__main__":
    import sys

    # Get markdown file from command line or default
    md_file = sys.argv[1] if len(sys.argv) > 1 else "examples/README.md"

    # Render the markdown
    output = render_markdown(md_file)
    print(output)
