# Image-generated vertical sheet vertical-0006

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0006.png` (`79db55069acadc6dcd145ab999dc049ebcab796311349e7c5351925418d32e7c`)
- State: awaiting generation

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original vertical-writing alternates in the Clear Hand TC family

Input images:
1. Image 1 is STYLE ONLY. Match its fine black gel-pen weight, rounded terminals, controlled handwritten rhythm, white background, and faint 4×4 grid. Do not copy its Han characters.
2. Image 2 is IDENTITY REFERENCE ONLY. Each cell shows the intended vertical-writing form using neutral reference fonts or a reference-only orientation transform. Never trace or import its printed outlines.

Draw exactly 13 independently authored vertical alternate glyphs in strict row-major order. These are new unencoded `.vert` glyphs, not mechanically rotated copies of the horizontal Clear Hand TC glyphs. Redraw each form naturally for vertical typography.

Critical orientation rule: every LEFT/RIGHT bracket or delimiter must use the TOP/BOTTOM vertical form visibly shown in Image 2. The opening left form becomes a top form opening downward; the closing right form becomes a bottom form opening upward. For example, `〈` must become `∧` and `〉` must become `∨`. Never retain a sideways `<`, `>`, `(`, `)`, `「`, `」`, or other left/right bracket silhouette in the output.

Critical Cell 01–02 rule: these two vertical alternates are side-by-side punctuation arrangements on one horizontal baseline. Cell 01 must be `•  •` from left to right. Cell 02 must be a comma-like mark on the left and one dot on the right. Never arrange either cell as a top/bottom vertical stack.

Exact occupied cells:
- Cell 01: `U+FF1A` FULLWIDTH COLON — base `：` — alternate `uniFF1A.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw exactly two round dots aligned horizontally in the vertical form.
- Cell 02: `U+FF1B` FULLWIDTH SEMICOLON — base `；` — alternate `uniFF1B.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the comma-like mark on the left and the round dot on the right, aligned horizontally; never stack them vertically.
- Cell 03: `U+FF1F` FULLWIDTH QUESTION MARK — base `？` — alternate `uniFF1F.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 04: `U+FF3B` FULLWIDTH LEFT SQUARE BRACKET — base `［` — alternate `uniFF3B.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a three-sided top square bracket opening downward.
- Cell 05: `U+FF3D` FULLWIDTH RIGHT SQUARE BRACKET — base `］` — alternate `uniFF3D.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a three-sided bottom square bracket opening upward.
- Cell 06: `U+FF3F` FULLWIDTH LOW LINE — base `＿` — alternate `uniFF3F.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw one straight vertical line, not a horizontal low line.
- Cell 07: `U+FF5B` FULLWIDTH LEFT CURLY BRACKET — base `｛` — alternate `uniFF5B.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the top horizontal curly-brace form shown in Image 2.
- Cell 08: `U+FF5C` FULLWIDTH VERTICAL LINE — base `｜` — alternate `uniFF5C.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw one straight horizontal line, not a vertical line.
- Cell 09: `U+FF5D` FULLWIDTH RIGHT CURLY BRACKET — base `｝` — alternate `uniFF5D.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the bottom horizontal curly-brace form shown in Image 2.
- Cell 10: `U+FF5E` FULLWIDTH TILDE — base `～` — alternate `uniFF5E.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw one vertical S-shaped tilde, not a horizontal wave.
- Cell 11: `U+FF5F` FULLWIDTH LEFT WHITE PARENTHESIS — base `｟` — alternate `uniFF5F.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the outlined top white-parenthesis form opening downward.
- Cell 12: `U+FF60` FULLWIDTH RIGHT WHITE PARENTHESIS — base `｠` — alternate `uniFF60.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the outlined bottom white-parenthesis form opening upward.
- Cell 13: `U+FFE3` FULLWIDTH MACRON — base `￣` — alternate `uniFFE3.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw one straight vertical macron line.

Unused cells: the final 3 trailing cell(s); leave them completely blank.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
