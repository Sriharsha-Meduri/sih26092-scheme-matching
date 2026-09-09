"""Structured, fact-backed explanation kernels (reason key lookup)."""

from intelligence.explanations.generator import (
    attach_to_recommendation,
    collect_reasons,
    collect_sources,
)

__all__ = ["collect_reasons", "collect_sources", "attach_to_recommendation"]