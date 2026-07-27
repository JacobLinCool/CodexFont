# Image-generated vertical sheet vertical-0001

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0001.png` (`4db5f7f128a2740d7b69c03546d576b29f432a9644d6f20d4da942a3b5f31cda`)
- State: awaiting generation

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original vertical-writing alternates in the Clear Hand TC family

Input images:
1. Image 1 is STYLE ONLY. Match its fine black gel-pen weight, rounded terminals, controlled handwritten rhythm, white background, and faint 4×4 grid. Do not copy its Han characters.
2. Image 2 is IDENTITY REFERENCE ONLY. Each cell shows the intended vertical-writing form using neutral reference fonts or a reference-only orientation transform. Never trace or import its printed outlines.

Draw exactly 16 independently authored vertical alternate glyphs in strict row-major order. These are new unencoded `.vert` glyphs, not mechanically rotated copies of the horizontal Clear Hand TC glyphs. Redraw each form naturally for vertical typography.

Critical orientation rule: every LEFT/RIGHT bracket or delimiter must use the TOP/BOTTOM vertical form visibly shown in Image 2. The opening left form becomes a top form opening downward; the closing right form becomes a bottom form opening upward. For example, `〈` must become `∧` and `〉` must become `∨`. Never retain a sideways `<`, `>`, `(`, `)`, `「`, `」`, or other left/right bracket silhouette in the output.

Exact occupied cells:
- Cell 01: `U+2013` EN DASH — base `–` — alternate `uni2013.vert` — VO `Tailored` — vertical en dash: a short upright vertical stroke.
- Cell 02: `U+2014` EM DASH — base `—` — alternate `uni2014.vert` — VO `Tailored` — vertical em dash: a long upright vertical stroke.
- Cell 03: `U+2018` LEFT SINGLE QUOTATION MARK — base `‘` — alternate `uni2018.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 04: `U+2019` RIGHT SINGLE QUOTATION MARK — base `’` — alternate `uni2019.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 05: `U+201C` LEFT DOUBLE QUOTATION MARK — base `“` — alternate `uni201C.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 06: `U+201D` RIGHT DOUBLE QUOTATION MARK — base `”` — alternate `uni201D.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 07: `U+2025` TWO DOT LEADER — base `‥` — alternate `uni2025.vert` — VO `Tailored` — two-dot leader: two vertically stacked dots.
- Cell 08: `U+2026` HORIZONTAL ELLIPSIS — base `…` — alternate `uni2026.vert` — VO `Tailored` — ellipsis: three vertically stacked dots.
- Cell 09: `U+2032` PRIME — base `′` — alternate `uni2032.vert` — VO `Tailored` — prime: vertical-writing prime orientation.
- Cell 10: `U+2035` REVERSED PRIME — base `‵` — alternate `uni2035.vert` — VO `Tailored` — reversed prime: vertical-writing reversed-prime orientation.
- Cell 11: `U+2219` BULLET OPERATOR — base `∙` — alternate `uni2219.vert` — VO `Tailored` — bullet operator: centered round dot for vertical mathematics.
- Cell 12: `U+2329` LEFT-POINTING ANGLE BRACKET — base `〈` — alternate `uni2329.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 13: `U+232A` RIGHT-POINTING ANGLE BRACKET — base `〉` — alternate `uni232A.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 14: `U+2574` BOX DRAWINGS LIGHT LEFT — base `╴` — alternate `uni2574.vert` — VO `Tailored` — box-drawing left half-line transformed to its vertical counterpart; draw one straight vertical half-line only; no horizontal segment, corner, hook, or L shape.
- Cell 15: `U+3001` IDEOGRAPHIC COMMA — base `、` — alternate `uni3001.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 16: `U+3002` IDEOGRAPHIC FULL STOP — base `。` — alternate `uni3002.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.

Unused cells: none.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
