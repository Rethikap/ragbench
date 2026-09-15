"""The evaluation set: 20 hand-verified questions with character-span labels.

A gold passage is ``(pmcid, char_start, char_end)`` into ``ParsedPaper.body``,
never a chunk id -- invariant I5. Nothing in this package imports a chunker, and
nothing here knows how either arm draws boundaries, which is what keeps the
labels comparable across the arms the experiment compares.
"""

from __future__ import annotations

from .passages import Passage, candidates, sample
from .validate import check, document_frequency

__all__ = ["Passage", "candidates", "check", "document_frequency", "sample"]
