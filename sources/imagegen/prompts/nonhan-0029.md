# Image-generated non-Han sheet nonhan-0029

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0029.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P16-MARK-COMBINING`
- Metric/design profiles: `nonspacing-mark`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0029.png` (`979ed7be0839b109a78dbacb0240edf1302287f4a7eb63053f45d5aaf258b8a2`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0029.png`, SHA-256 `979ed7be0839b109a78dbacb0240edf1302287f4a7eb63053f45d5aaf258b8a2`) is IDENTITY
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
- Cell 01: `U+0310` COMBINING CANDRABINDU — character `̐` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 02: `U+0311` COMBINING INVERTED BREVE — character `̑` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 03: `U+0312` COMBINING TURNED COMMA ABOVE — character `̒` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 04: `U+0313` COMBINING COMMA ABOVE — character `̓` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 05: `U+0314` COMBINING REVERSED COMMA ABOVE — character `̔` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 06: `U+0315` COMBINING COMMA ABOVE RIGHT — character `̕` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-232"}`
- Cell 07: `U+0316` COMBINING GRAVE ACCENT BELOW — character `̖` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 08: `U+0317` COMBINING ACUTE ACCENT BELOW — character `̗` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 09: `U+0318` COMBINING LEFT TACK BELOW — character `̘` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 10: `U+0319` COMBINING RIGHT TACK BELOW — character `̙` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 11: `U+031A` COMBINING LEFT ANGLE ABOVE — character `̚` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-232"}`
- Cell 12: `U+031B` COMBINING HORN — character `̛` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-216"}`
- Cell 13: `U+031C` COMBINING LEFT HALF RING BELOW — character `̜` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 14: `U+031D` COMBINING UP TACK BELOW — character `̝` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 15: `U+031E` COMBINING DOWN TACK BELOW — character `̞` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 16: `U+031F` COMBINING PLUS SIGN BELOW — character `̟` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`

Unused cells: All sixteen cells are occupied.

Identity-critical anatomy:
- Draw only the isolated mark shown in each copybook cell, with no carrier.
- Cell 01 is an upward-opening small cup with one filled dot above it; Cell 02
  is the opposite, a downward-opening cap with no dot.
- Cells 09 and 10 are mirror tacks: one vertical stem with a short horizontal
  extending only left, then only right.
- Cell 11 is a right-angle corner with its horizontal extending left from the
  top of a descending right stem.
- Cell 12 is the compact right-side horn shown in the copybook: one descending
  comma-like hook with a short top stem. It is not a U, cup, or half ring.
- Cell 13 is a left half ring shaped like a `C` opening right.
- Cell 14 is an up tack, a horizontal baseline with a vertical rising from its
  center (`⊥`); Cell 15 is the opposite down tack (`T`).
- Cell 16 is one plus sign.

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
