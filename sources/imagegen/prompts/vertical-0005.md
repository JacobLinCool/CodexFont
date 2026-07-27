# Image-generated vertical sheet vertical-0005

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0005.png` (`a12d7449b39c0eb60b15daa98dc686ac904db86648ed42cb6fd87ceb31c2c994`)
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
- Cell 01: `U+30F5` KATAKANA LETTER SMALL KA — base `ヵ` — alternate `uni30F5.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 02: `U+30F6` KATAKANA LETTER SMALL KE — base `ヶ` — alternate `uni30F6.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 03: `U+30FC` KATAKANA-HIRAGANA PROLONGED SOUND MARK — base `ー` — alternate `uni30FC.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw one straight vertical line for the vertical prolonged-sound mark.
- Cell 04: `U+3127` BOPOMOFO LETTER I — base `ㄧ` — alternate `uni3127.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback; keep Bopomofo I as one straight horizontal line; do not rotate it.
- Cell 05: `U+31B4` BOPOMOFO FINAL LETTER P — base `ㆴ` — alternate `uni31B4.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 06: `U+31B5` BOPOMOFO FINAL LETTER T — base `ㆵ` — alternate `uni31B5.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 07: `U+31B6` BOPOMOFO FINAL LETTER K — base `ㆶ` — alternate `uni31B6.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 08: `U+31B7` BOPOMOFO FINAL LETTER H — base `ㆷ` — alternate `uni31B7.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 09: `U+31BB` BOPOMOFO FINAL LETTER G — base `ㆻ` — alternate `uni31BB.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 10: `U+FE4F` WAVY LOW LINE — base `﹏` — alternate `uniFE4F.vert` — VO `Tailored` — wavy low line transformed into a vertical wavy rule; draw one slender vertical wavy rule, never a horizontal underline.
- Cell 11: `U+FE55` SMALL COLON — base `﹕` — alternate `uniFE55.vert` — VO `Tailored` — small colon optically centered for vertical CJK text; draw exactly two small round dots stacked vertically.
- Cell 12: `U+FF01` FULLWIDTH EXCLAMATION MARK — base `！` — alternate `uniFF01.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 13: `U+FF08` FULLWIDTH LEFT PARENTHESIS — base `（` — alternate `uniFF08.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a top parenthesis arc opening downward, never a sideways `(`.
- Cell 14: `U+FF09` FULLWIDTH RIGHT PARENTHESIS — base `）` — alternate `uniFF09.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a bottom parenthesis arc opening upward, never a sideways `)`.
- Cell 15: `U+FF0C` FULLWIDTH COMMA — base `，` — alternate `uniFF0C.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 16: `U+FF0E` FULLWIDTH FULL STOP — base `．` — alternate `uniFF0E.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.

Unused cells: none.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
