"""Custom formatter for PyDoV4 - composes TextKit components."""

from replkit2.textkit import TextFormatter, box, compose, hr, config
from replkit2.types import CommandMeta


class PyDoV4Formatter(TextFormatter):
    """PyDoV4 formatter with custom display for code diagnostics."""

    def __init__(self):
        super().__init__()
        self._register_pydov4_handlers()

    def _register_pydov4_handlers(self):
        """Register custom handlers for PyDoV4-specific displays."""

        @self.register("custom:code_diagnostics")
        def handle_code_diagnostics(data: dict, meta: CommandMeta) -> str:
            """Display code with inline diagnostics using TextKit components."""
            if "error" in data:
                return box(data["error"], title="Error")

            # Extract data
            file_path = data.get("file_path", "Unknown")
            start_line = data.get("start_line", 1)
            end_line = data.get("end_line", start_line)
            code_lines = data.get("lines", [])
            diagnostics = data.get("diagnostics", {})

            # Build header
            header = f"File: {file_path} (lines {start_line}-{end_line})"

            # Build code section with diagnostics
            formatted_lines = []
            line_prefix = " " * 6  # Indentation for diagnostic messages

            for i, code_line in enumerate(code_lines):
                line_num = start_line + i

                # Check for diagnostics on this line (0-based in diagnostics dict)
                line_diags = diagnostics.get(line_num - 1, [])

                if line_diags:
                    severity = line_diags[0]["short"]
                    formatted_lines.append(f"{line_num:4d} {severity} | {code_line}")

                    for diag in line_diags:
                        msg = diag["message"]
                        max_msg_width = config.width - len(line_prefix) - 4
                        if len(msg) > max_msg_width:
                            msg = msg[: max_msg_width - 3] + "..."
                        formatted_lines.append(f"{line_prefix} | ^ {diag['severity']}: {msg}")
                else:
                    formatted_lines.append(f"{line_num:4d}   | {code_line}")

            code_section = "\n".join(formatted_lines)

            # Compose the final output
            return compose(
                header,
                hr(),
                code_section,
                spacing=0,  # No extra spacing between components
            )
