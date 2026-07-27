# QA and release gates

## Raster gate

- Exact cell-to-glyph identity and sequence.
- Correct script topology and semantic role.
- No missing or extra strokes, marks, fills, counters, or components.
- No grid contact, clipping, detached noise, accidental decoration, or polarity
  inversion.
- Legibility after reduction to each intended use size.

## Vector gate

Recompute from emitted outlines:

- simple/composite policy;
- contour and point counts;
- bounds and side bearings;
- winding, counters, and edge-connected topology;
- minimum non-degenerate edge;
- acute micro-turn and spike signatures;
- self-intersections, zero-area contours, and cropped ink;
- raster coverage at proof sizes.

Never trust a report field that can be recomputed from the font.

## Review gate

Render both black-on-white and white-on-black. Review isolated glyphs and
context strings at every contract size. Record one explicit result per glyph.
Keep reviewer records immutable and separate from generator/build reports.

## Approval gate

Pin exact relative paths and SHA-256 values for:

- repertoire and descriptor;
- raster and prompt;
- copybook/style references;
- vector report and complete artifact inventory;
- preview fonts and proofs;
- reviewer record;
- final authorization.

Reject unknown fields, path traversal, symlinks, duplicate records, stale
proofs, changed inventories, and mismatched hashes.

The approved inventory does not require every derived file to stay in Git.
Keep the report and final review proofs. Regenerate per-glyph previews, SVGs,
JSON extracts, and preview fonts in an ignored cache, then require exact hashes.
Use LFS only for large originals that cannot be recreated.

## OpenType gate

Validate every shipped format:

- glyph order, `cmap`, outlines, horizontal and vertical metrics;
- `.notdef` and semantic-empty glyph policy;
- names, version, embedding, license, underline, strikeout, caret metadata;
- required GDEF/GPOS/GSUB features and substitutions;
- shaping with a production shaper;
- absence of undeclared encoded glyphs or fallback outlines.

## Release gate

- Build into a staging directory and install atomically with rollback.
- Build twice and compare every artifact byte-for-byte.
- Render complete coverage proofs and representative specimens.
- Load the final webfont in a browser with zero console or network errors.
- Publish the exact coverage denominator and missing set.
