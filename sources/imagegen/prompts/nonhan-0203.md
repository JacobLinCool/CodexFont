# Image-generated non-Han sheet nonhan-0203

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0203.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P63-BLOCK-ELEMENTS`
- Metric/design profiles: `block-element`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0203.png` (`c1bb5079c0f601ef44585b9b43dca22dc54a05780bbfc4c68aeeb6695528b959`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0203.png`, SHA-256 `c1bb5079c0f601ef44585b9b43dca22dc54a05780bbfc4c68aeeb6695528b959`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P63-BLOCK-ELEMENTS`
Metric/design profiles present: `block-element`
- [block-element] Preserve the exact fill fraction, edge, quadrant, and light/dark state; do not round away functional coverage boundaries.
- [block-element] Keep the authored fill centered and clearly separated from the gray grid while preserving exact relative fractions. The vector stage will normalize its Unicode-defined bounds to exact em-boundary coordinates.

Exact occupied cells:
- Cell 01: `U+2580` UPPER HALF BLOCK — character `▀` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2581` LOWER ONE EIGHTH BLOCK — character `▁` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2582` LOWER ONE QUARTER BLOCK — character `▂` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2583` LOWER THREE EIGHTHS BLOCK — character `▃` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2584` LOWER HALF BLOCK — character `▄` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2585` LOWER FIVE EIGHTHS BLOCK — character `▅` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2586` LOWER THREE QUARTERS BLOCK — character `▆` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2587` LOWER SEVEN EIGHTHS BLOCK — character `▇` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2588` FULL BLOCK — character `█` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2589` LEFT SEVEN EIGHTHS BLOCK — character `▉` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+258A` LEFT THREE QUARTERS BLOCK — character `▊` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+258B` LEFT FIVE EIGHTHS BLOCK — character `▋` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+258C` LEFT HALF BLOCK — character `▌` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+258D` LEFT THREE EIGHTHS BLOCK — character `▍` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+258E` LEFT ONE QUARTER BLOCK — character `▎` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+258F` LEFT ONE EIGHTH BLOCK — character `▏` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Block-element topology and fraction requirements:
- These are functional rectangular fills. Use axis-aligned straight coverage
  boundaries and square corners; no rounded edge, outline, gray wash, or
  handwritten wobble. Keep a consistent inset construction safely inside
  every cell so the grid remains unobstructed.
- Cell 01 fills exactly the UPPER half of its common source box. Cells 02–08
  are BOTTOM-aligned fills of exactly 1/8, 1/4, 3/8, 1/2, 5/8, 3/4, and 7/8
  of one identical common source-box height.
- Cell 09 is a solid full source box. Cells 10–16 are LEFT-aligned fills of
  exactly 7/8, 3/4, 5/8, 1/2, 3/8, 1/4, and 1/8 of one identical common
  source-box width.
- The raster supplies original fill identity and exact relative fractions.
  Standard v3 vector metric normalization later maps required outer bounds to
  the em edges and fractional boundaries to exact eighth coordinates.

Unused cells: All sixteen cells are occupied.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep all black source ink
well away from separators. Exact Unicode edge placement and fractional
coordinates are applied later as standard vector metric normalization; the
raster must supply the original fill identity and relative proportions. Use
pure white with no texture, gradient, lighting, or shadow.

Constraints: preserve every requested Unicode identity, direction, topology,
dot, line count, enclosure, fill state, and paired distinction; output each
target exactly once and only in its assigned cell; keep the style handwritten
and legible at small text sizes. The identity copybook is evidence, never an
outline source.

Do not include any U+XXXX label, Unicode name, cell number, caption, legend,
dotted-circle carrier, annotation, signature, logo, or watermark. Do not
render anything in unused cells. Avoid typeset appearance, brush blobs, dry
brush, ink splatter, sharp miter spikes, thorn-like protrusions, clipping,
duplicate glyphs, missing glyphs, reordered cells, or unintended black bridges
between neighboring cells.
```
