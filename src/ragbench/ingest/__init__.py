"""Corpus selection and JATS ingest.

The only package in the project permitted to touch the network, and only in
:mod:`ragbench.ingest.ncbi`. Everything downstream reads the frozen manifest and
the on-disk caches this package produces.
"""

from __future__ import annotations
