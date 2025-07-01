"""Core text manipulation utilities."""

from .config import config


def truncate(text: str, width: int | None = None, suffix: str = "...") -> str:
    """Truncate text to fit within width, adding suffix if truncated."""
    width = width or config.width

    if len(text) <= width:
        return text

    if len(suffix) >= width:
        return text[:width]

    return text[: width - len(suffix)] + suffix


def align(text: str, width: int | None = None, mode: str = "left") -> str:
    """Align text within width. Mode: 'left', 'right', 'center'."""
    width = width or config.width

    if len(text) >= width:
        return truncate(text, width)

    if mode == "left":
        return text.ljust(width)
    elif mode == "right":
        return text.rjust(width)
    elif mode == "center":
        return text.center(width)
    else:
        raise ValueError(f"Invalid align mode: {mode}")


def wrap(text: str, width: int | None = None) -> list[str]:
    """Wrap text into lines of maximum width."""
    width = width or config.width

    if not text:
        return []

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)

        # If word itself is too long, break it
        if word_length > width:
            # Finish current line if any
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
                current_length = 0

            # Break the word
            for i in range(0, word_length, width):
                lines.append(word[i : i + width])

        # If adding word exceeds width, start new line
        elif current_length + word_length + len(current_line) > width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length

        # Add word to current line
        else:
            current_line.append(word)
            current_length += word_length

    # Add remaining words
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def indent(text: str, level: int = 1, char: str = " ") -> str:
    """Indent each line of text."""
    spaces = char * (level * config.indent)
    lines = text.split("\n")
    return "\n".join(spaces + line if line else line for line in lines)
