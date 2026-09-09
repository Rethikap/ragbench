"""Version stamps that invalidate caches when behaviour changes.

Bump PARSER_VERSION whenever ingest/jats.py changes what text it produces; bump
CHUNKER_VERSION whenever a chunker changes how it draws boundaries. Both feed into
on-disk cache keys, so a bump silently forces a rebuild instead of silently mixing
old and new artefacts.
"""

from __future__ import annotations

PARSER_VERSION = "2"
CHUNKER_VERSION = "1"
CONFIG_SCHEMA_VERSION = 1
