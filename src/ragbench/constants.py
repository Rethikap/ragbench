"""Version stamps that invalidate caches when behaviour changes.

Bump PARSER_VERSION whenever ingest/jats.py changes what text it produces; bump
CHUNKER_VERSION whenever a chunker changes how it draws boundaries. Both feed into
on-disk cache keys, so a bump silently forces a rebuild instead of silently mixing
old and new artefacts.
"""

from __future__ import annotations

# 2 -> 3: brackets left empty by citation removal are stripped. JATS marks a
# citation as either <xref>[1]</xref>, which disappears cleanly, or
# [<xref>1</xref>], which left "[]" in the prose -- 3,863 of them, in 80 of the
# 100 papers. Changes the body stream and therefore every character offset in it.
PARSER_VERSION = "3"
# 1 -> 2: windows are trimmed to the token target after slicing. A window cut
# mid-word re-tokenizes to more tokens than it contains, so the fixed arm was
# emitting 513-514-token chunks against a 512 target (54 of 1,586) while the
# recursive arm, which cuts on separators, emitted none. See chunking.base.fit_window.
CHUNKER_VERSION = "2"
CONFIG_SCHEMA_VERSION = 1
