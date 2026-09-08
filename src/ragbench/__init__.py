"""Controlled 2x2x2 factorial benchmark of RAG design choices for scientific-literature QA.

Deliberately empty of re-exports. Later submodules pull torch, transformers and
chromadb; keeping this module stdlib-only means `import ragbench` -- and therefore
CLI startup and the CPU smoke path -- never drags in a GPU dependency.
"""

from __future__ import annotations

__version__ = "0.1.0"
