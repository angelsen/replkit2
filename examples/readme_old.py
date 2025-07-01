#!/usr/bin/env python3
"""
README renderer - converts markdown to ASCII art using TextKit.

Usage:
    uv run python examples/readme.py > ../README.md

This demonstrates TextKit's display capabilities by rendering
a markdown file as pure ASCII.
"""

import re
from pathlib import Path
from replkit2.textkit import box, table, list_display, hr, compose, align, config

# Set page width for nice formatting
config.width = 80


def render_markdown(md_path: str) -> str:
    """Render a markdown file as ASCII art."""
    content = Path(md_path).read_text()
    sections = []

    # Split into lines for processing
    lines = content.split("\n")
    i = 0

    # Check if the last non-empty line is the "Built with" tagline
    has_built_with = False
    for line in reversed(lines):
        if line.strip():
            if "Built with" in line and "❤️" in line:
                has_built_with = True
            break

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip the final "---" and "Built with" if present
        if line.strip() == "---" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and "Built with" in next_line and "❤️" in next_line:
                # Skip both the hr and the Built with line
                break

        # Headers
        if line.startswith("# "):
            # H1 - Big box full width with hr
            title = line[2:].strip()
            sections.append(
                compose(
                    box(title.upper(), title="H1", width=config.width),
                    hr("-"),
                    spacing=0,
                )
            )
            i += 1

        elif line.startswith("## "):
            # H2 - Full width box with hr
            title = line[3:].strip()
            sections.append(compose(box(title, title="H2", width=config.width), hr("-"), spacing=0))
            i += 1

        elif line.startswith("### "):
            # H3 - Full width box with hr
            title = line[4:].strip()
            sections.append(compose(box(title, title="H3", width=config.width), hr("-"), spacing=0))
            i += 1

        # Horizontal rule
        elif line.strip() in ["---", "***", "___"]:
            sections.append(hr("="))
            i += 1

        # Code blocks
        elif line.strip().startswith("```"):
            # Find end of code block
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1

            if code_lines:
                code_content = "\n".join(code_lines)
                sections.append(box(code_content, title="CODE", width=config.width))
            i += 1

        # Tables
        elif "|" in line and i + 1 < len(lines) and "|" in lines[i + 1] and "-" in lines[i + 1]:
            # Parse table
            headers = [cell.strip() for cell in line.split("|")[1:-1]]
            i += 2  # Skip separator

            rows = []
            while i < len(lines) and "|" in lines[i]:
                row = [cell.strip() for cell in lines[i].split("|")[1:-1]]
                rows.append(row)
                i += 1

            sections.append(table(rows, headers))

        # Lists
        elif line.strip().startswith(("- ", "* ", "+ ")):
            # Collect list items
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
                item = lines[i].strip()[2:]
                items.append(item)
                i += 1

            sections.append(list_display(items, style="bullet"))

        # Numbered lists
        elif re.match(r"^\d+\.\s", line.strip()):
            # Collect numbered items
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(item)
                i += 1

            sections.append(list_display(items, numbered=True))

        # Regular paragraphs
        elif line.strip():
            # Collect paragraph lines
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "-", "*", "```", "|")):
                para_lines.append(lines[i].strip())
                i += 1

            if para_lines:
                paragraph = " ".join(para_lines)

                # Skip if this is the "Built with" tagline at the end
                if "Built with" in paragraph and "❤️" in paragraph and has_built_with:
                    continue

                # Handle inline code
                paragraph = re.sub(r"`([^`]+)`", r"[\1]", paragraph)

                # Handle bold
                paragraph = re.sub(r"\*\*([^*]+)\*\*", r"\1", paragraph)
                paragraph = re.sub(r"__([^_]+)__", r"\1", paragraph)

                # Handle italic (just remove markers)
                paragraph = re.sub(r"\*([^*]+)\*", r"\1", paragraph)
                paragraph = re.sub(r"_([^_]+)_", r"\1", paragraph)

                # Wrap paragraph to page width
                from replkit2.textkit import wrap

                wrapped_lines = wrap(paragraph, config.width)
                sections.extend(wrapped_lines)
        else:
            i += 1

    # Compose final document with proper spacing
    header = compose(
        hr("="),
        align("ReplKit2 - README", mode="center"),
        align("Rendered with TextKit", mode="center"),
        hr("="),
        spacing=1,
    )

    footer = compose(
        hr("="),
        align("Built with ❤️ for the Python REPL", mode="center"),
        hr("="),
        align("Generated from examples/README.md", mode="center"),
        hr("="),
        spacing=1,
    )

    # Use spacing=1 to automatically add blank lines between major sections
    return compose(header, *sections, footer, spacing=1)


if __name__ == "__main__":
    # Render the README
    output = render_markdown("examples/README.md")
    print(output)

    # Also save to root
    with open("README", "w") as f:
        f.write(output)
