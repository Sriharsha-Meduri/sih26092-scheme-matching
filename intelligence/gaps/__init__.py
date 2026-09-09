"""Deterministic gap detection (M2 §11, §13)."""

from intelligence.gaps.detector import aggregate_missing_fields, detect_missing_fields

__all__ = ["detect_missing_fields", "aggregate_missing_fields"]