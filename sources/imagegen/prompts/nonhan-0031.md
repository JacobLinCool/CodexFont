# Image-generated non-Han sheet nonhan-0031

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0031.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P16-MARK-COMBINING`
- Metric/design profiles: `nonspacing-mark`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0031.png` (`dfe8586899bc61973d61ab94ac74aa36a40a570c7c4c3e950af7180578c4513e`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0031.png`, SHA-256 `dfe8586899bc61973d61ab94ac74aa36a40a570c7c4c3e950af7180578c4513e`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P16-MARK-COMBINING`
Metric/design profiles present: `nonspacing-mark`
- [nonspacing-mark] Draw only the requested combining-mark ink, enlarged enough to identify in its cell; do not add a base, dotted circle, or carrier glyph.
- [nonspacing-mark] The final font metric is zero advance; the raster cell is an identity capture canvas, not evidence of final spacing.

Exact occupied cells:
- Cell 01: `U+0330` COMBINING TILDE BELOW — character `̰` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 02: `U+0331` COMBINING MACRON BELOW — character `̱` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 03: `U+0332` COMBINING LOW LINE — character `̲` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 04: `U+0333` COMBINING DOUBLE LOW LINE — character `̳` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 05: `U+0334` COMBINING TILDE OVERLAY — character `̴` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-1"}`
- Cell 06: `U+0335` COMBINING SHORT STROKE OVERLAY — character `̵` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-1"}`
- Cell 07: `U+0336` COMBINING LONG STROKE OVERLAY — character `̶` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-1"}`
- Cell 08: `U+0337` COMBINING SHORT SOLIDUS OVERLAY — character `̷` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-1"}`
- Cell 09: `U+0338` COMBINING LONG SOLIDUS OVERLAY — character `̸` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-1"}`
- Cell 10: `U+0339` COMBINING RIGHT HALF RING BELOW — character `̹` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 11: `U+033A` COMBINING INVERTED BRIDGE BELOW — character `̺` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 12: `U+033B` COMBINING SQUARE BELOW — character `̻` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 13: `U+033C` COMBINING SEAGULL BELOW — character `̼` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 14: `U+033D` COMBINING X ABOVE — character `̽` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 15: `U+033E` COMBINING VERTICAL TILDE — character `̾` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 16: `U+033F` COMBINING DOUBLE OVERLINE — character `̿` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`

Unused cells: All sixteen cells are occupied.

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
