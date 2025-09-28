"""URI generation for MCP resources."""

import re
from typing import Callable

from .parameters import ParameterAnalyzer


class URIBuilder:
    """Build URIs for MCP resources."""

    def __init__(self, scheme: str):
        self.scheme = scheme
        self.analyzer = ParameterAnalyzer()

    def build_simple(self, func: Callable) -> str:
        """Build URI with direct parameter mapping."""
        base_uri = f"{self.scheme}://{func.__name__}"
        required_params = self.analyzer.get_required_parameters(func)

        if required_params:
            base_uri += "/" + "/".join(f"{{{p.name}}}" for p in required_params)

        return base_uri

    def build_greedy(self, func: Callable) -> str:
        """Build URI with greedy pattern for optional parameters."""
        base_uri = f"{self.scheme}://{func.__name__}"
        required_params = self.analyzer.get_required_parameters(func)

        if required_params:
            base_uri += "/" + "/".join(f"{{{p.name}}}" for p in required_params)

        # Add greedy pattern for optional parameters
        base_uri += "/{params*}"

        return base_uri

    def build_stub(self, func: Callable, template: str) -> str:
        """Build stub URI with example notation."""
        if "{params*}" in template:
            # For greedy URIs, show parameter structure
            base = template.replace("/{params*}", "")
            optional_params = self.analyzer.get_optional_parameters(func)

            for param in optional_params:
                base += f"/[:{param.name}]"

            return base
        else:
            # Standard parameter substitution
            return re.sub(r"\{(\w+)\}", r":\1", template)
