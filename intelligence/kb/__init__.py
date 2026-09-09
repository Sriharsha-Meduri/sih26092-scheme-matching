"""Knowledge Base access layer (read-only, per M0 Component Contracts §5).

Only this package reads KB/normalized/*. Everything upstream (normalization,
eligibility, matching, ranking) consumes the typed repository. No writes.
"""

from intelligence.kb.loader import KBError, KBIntegrityError, load_normalized
from intelligence.kb.repository import KnowledgeBase

__all__ = ["KBError", "KBIntegrityError", "KnowledgeBase", "load_normalized"]