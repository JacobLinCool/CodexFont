# Image-generated non-Han sheet nonhan-0034

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0034.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P16-MARK-COMBINING`
- Metric/design profiles: `nonspacing-mark`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0034.png` (`3869be0d774098c627b745a00d1ba5122fe9c769418499ee1c40d83983d052c7`)
- Copybook role: identity-reference-only-no-outline-import
- State: awaiting generation; all review gates pending

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original non-Han
glyphs in the Clear Hand TC family

Input images:
1. Image 1 (`sources/imagegen/raster/common-0001.png`, SHA-256 `2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`) is STYLE ONLY.
   Match its fine black gel-pen weight, rounded terminals, natural but
   controlled handwriting rhythm, optical scale, pure-white background, and
   faint 4×4 grid. Do not copy its Han characters.
2. Image 2 (`sources/imagegen/copybooks/nonhan-0034.png`, SHA-256 `3869be0d774098c627b745a00d1ba5122fe9c769418499ee1c40d83983d052c7`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 10 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P16-MARK-COMBINING`
Metric/design profiles present: `nonspacing-mark`
- [nonspacing-mark] Draw only the requested combining-mark ink, enlarged enough to identify in its cell; do not add a base, dotted circle, or carrier glyph.
- [nonspacing-mark] The final font metric is zero advance; the raster cell is an identity capture canvas, not evidence of final spacing.

Exact occupied cells:
- Cell 01: `U+0366` COMBINING LATIN SMALL LETTER O — character `ͦ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 02: `U+0367` COMBINING LATIN SMALL LETTER U — character `ͧ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 03: `U+0368` COMBINING LATIN SMALL LETTER C — character `ͨ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 04: `U+0369` COMBINING LATIN SMALL LETTER D — character `ͩ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 05: `U+036A` COMBINING LATIN SMALL LETTER H — character `ͪ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 06: `U+036B` COMBINING LATIN SMALL LETTER M — character `ͫ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 07: `U+036C` COMBINING LATIN SMALL LETTER R — character `ͬ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 08: `U+036D` COMBINING LATIN SMALL LETTER T — character `ͭ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 09: `U+036E` COMBINING LATIN SMALL LETTER V — character `ͮ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 10: `U+036F` COMBINING LATIN SMALL LETTER X — character `ͯ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`

Unused cells: Cells 11–16 are intentionally unused and must remain completely blank.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep all black ink well
away from separators. Use pure white with no texture, gradient, lighting, or
shadow.

Constraints: preserve every requested Unicode identity, direction, topology,
dot, line count, enclosure, fill state, and paired distinction; output each
target exactly once and only in its assigned cell; keep the style handwritten
and legible at small text sizes. The identity copybook is evidence, never an
outline source.

Do not include any U+XXXX label, Unicode name, cell number, caption, legend,
dotted-circle carrier, annotation, signature, logo, or watermark. Do not
render anything in unused cells. Avoid typeset appearance, brush blobs, dry
brush, ink splatter, sharp miter spikes, thorn-like protrusions, clipping,
duplicate glyphs, missing glyphs, reordered cells, or connected cells.
```
