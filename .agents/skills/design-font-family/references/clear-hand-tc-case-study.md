# Clear Hand TC case study

This repository proves the workflow at a 9,120-codepoint Traditional Chinese
handwriting milestone: 6,060 Han plus 3,060 non-Han codepoints.

## Evidence map

- Design and source policy: `README.md`, `docs/DESIGN.md`, `docs/SOURCES.md`
- Repertoires: `sources/imagegen/repertoires/`
- Original raster batches: `sources/imagegen/raster/`
- Batch descriptors and prompts: `sources/imagegen/batches/`,
  `sources/imagegen/prompts/`
- Build reports and final review proofs: `build/imagegen/imagegen-*/`
- Reviews and approvals: `sources/imagegen/vector-reviews/`,
  `sources/imagegen/approvals/`
- Release compiler: `scripts/build_imagegen_release_font.py`
- Machine-readable release evidence: `dist/clear-hand-tc/report.json`

## Proven sequence

1. Freeze 6,060 Traditional Chinese Han glyphs in three reviewed segments
   (3,000 common, 1,844 MOE extension, and 1,216 dictionary-salience
   extension), 3,060 non-Han encoded glyphs, and 93 unencoded vertical
   alternates.
2. Author visible glyphs as white-background, black-ink image-generation
   batches.
3. Vectorize to quadratic TrueType outlines and recompute geometry.
4. Review five small sizes in two polarities per source batch.
5. Admit only complete descriptor → raster → build → proof → review → approval
   hash chains.
6. Assemble 9,120 encoded glyphs (6,060 Han plus 3,060 non-Han), 93 vertical
   alternates, and `.notdef`.
7. Build TTF, OTF, WOFF, WOFF2, CSS, license, reports, and complete proofs twice
   with byte-identical output.
8. Keep original rasters, reports, approvals, and final review proofs. Rebuild
   per-glyph previews, SVGs, JSON extracts, and preview fonts in an ignored
   cache; LFS stores only irreplaceable large originals.

## Project-specific values

These values are evidence for this case, not defaults for other families:

- 4×4 visible-source sheets;
- 12, 16, 20, 32, and 56 px source proofs in both polarities;
- additional 24, 36, and 72 px release proofs;
- zero final micro-edges and acute micro-turns;
- `kern`, `mark`, `mkmk`, `vert`, and `vrt2`;
- SIL Open Font License 1.1.
