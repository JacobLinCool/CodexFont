# Image-generated vertical sheet vertical-0003

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0003.png` (`4918ea9b7ed37e1bc0d220db88e2b8b763a03d276bf3c6ffff86852fd3a86ff1`)
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
- Cell 01: `U+301A` LEFT WHITE SQUARE BRACKET — base `〚` — alternate `uni301A.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 02: `U+301B` RIGHT WHITE SQUARE BRACKET — base `〛` — alternate `uni301B.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 03: `U+301C` WAVE DASH — base `〜` — alternate `uni301C.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 04: `U+301D` REVERSED DOUBLE PRIME QUOTATION MARK — base `〝` — alternate `uni301D.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw exactly two short quote strokes total; do not duplicate them into two pairs.
- Cell 05: `U+301E` DOUBLE PRIME QUOTATION MARK — base `〞` — alternate `uni301E.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw exactly two short quote strokes total; do not duplicate them into two pairs.
- Cell 06: `U+301F` LOW DOUBLE PRIME QUOTATION MARK — base `〟` — alternate `uni301F.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw exactly two short quote strokes total; do not add a third stroke.
- Cell 07: `U+3030` WAVY DASH — base `〰` — alternate `uni3030.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 08: `U+3041` HIRAGANA LETTER SMALL A — base `ぁ` — alternate `uni3041.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 09: `U+3043` HIRAGANA LETTER SMALL I — base `ぃ` — alternate `uni3043.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 10: `U+3045` HIRAGANA LETTER SMALL U — base `ぅ` — alternate `uni3045.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 11: `U+3047` HIRAGANA LETTER SMALL E — base `ぇ` — alternate `uni3047.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 12: `U+3049` HIRAGANA LETTER SMALL O — base `ぉ` — alternate `uni3049.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 13: `U+3063` HIRAGANA LETTER SMALL TU — base `っ` — alternate `uni3063.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 14: `U+3083` HIRAGANA LETTER SMALL YA — base `ゃ` — alternate `uni3083.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 15: `U+3085` HIRAGANA LETTER SMALL YU — base `ゅ` — alternate `uni3085.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 16: `U+3087` HIRAGANA LETTER SMALL YO — base `ょ` — alternate `uni3087.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.

Unused cells: none.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
