# Image-generated vertical sheet vertical-0004

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0004.png` (`4c04e8e903eddb6d044813220da3424336d4b55429f74ef2dc08005333eefd30`)
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
- Cell 01: `U+308E` HIRAGANA LETTER SMALL WA — base `ゎ` — alternate `uni308E.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 02: `U+3095` HIRAGANA LETTER SMALL KA — base `ゕ` — alternate `uni3095.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 03: `U+3096` HIRAGANA LETTER SMALL KE — base `ゖ` — alternate `uni3096.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 04: `U+309B` KATAKANA-HIRAGANA VOICED SOUND MARK — base `゛` — alternate `uni309B.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 05: `U+309C` KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK — base `゜` — alternate `uni309C.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 06: `U+30A0` KATAKANA-HIRAGANA DOUBLE HYPHEN — base `゠` — alternate `uni30A0.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 07: `U+30A1` KATAKANA LETTER SMALL A — base `ァ` — alternate `uni30A1.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 08: `U+30A3` KATAKANA LETTER SMALL I — base `ィ` — alternate `uni30A3.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 09: `U+30A5` KATAKANA LETTER SMALL U — base `ゥ` — alternate `uni30A5.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 10: `U+30A7` KATAKANA LETTER SMALL E — base `ェ` — alternate `uni30A7.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 11: `U+30A9` KATAKANA LETTER SMALL O — base `ォ` — alternate `uni30A9.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 12: `U+30C3` KATAKANA LETTER SMALL TU — base `ッ` — alternate `uni30C3.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 13: `U+30E3` KATAKANA LETTER SMALL YA — base `ャ` — alternate `uni30E3.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 14: `U+30E5` KATAKANA LETTER SMALL YU — base `ュ` — alternate `uni30E5.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 15: `U+30E7` KATAKANA LETTER SMALL YO — base `ョ` — alternate `uni30E7.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.
- Cell 16: `U+30EE` KATAKANA LETTER SMALL WA — base `ヮ` — alternate `uni30EE.vert` — VO `Tu` — Unicode typographic vertical transform with upright fallback.

Unused cells: none.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
