# Image-generated non-Han sheet nonhan-0196

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0196.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P62-BOX-DRAWING`
- Metric/design profiles: `box-drawing`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0196.png` (`00504a3a6b2715809dce8be35ddfca99fabb7f68e3bac113f664297cf9a997a2`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0196.png`, SHA-256 `00504a3a6b2715809dce8be35ddfca99fabb7f68e3bac113f664297cf9a997a2`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P62-BOX-DRAWING`
Metric/design profiles present: `box-drawing`
- [box-drawing] Preserve every endpoint, junction, single/double line, and weight distinction exactly; connection topology outranks decorative variation.
- [box-drawing] Keep the authored topology centered and clearly separated from the gray grid. The vector stage will normalize each Unicode-required arm to its exact em boundary without replacing the generated outline.

Exact occupied cells:
- Cell 01: `U+2510` BOX DRAWINGS LIGHT DOWN AND LEFT — character `┐` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2511` BOX DRAWINGS DOWN LIGHT AND LEFT HEAVY — character `┑` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2512` BOX DRAWINGS DOWN HEAVY AND LEFT LIGHT — character `┒` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2513` BOX DRAWINGS HEAVY DOWN AND LEFT — character `┓` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2514` BOX DRAWINGS LIGHT UP AND RIGHT — character `└` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2515` BOX DRAWINGS UP LIGHT AND RIGHT HEAVY — character `┕` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2516` BOX DRAWINGS UP HEAVY AND RIGHT LIGHT — character `┖` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2517` BOX DRAWINGS HEAVY UP AND RIGHT — character `┗` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2518` BOX DRAWINGS LIGHT UP AND LEFT — character `┘` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2519` BOX DRAWINGS UP LIGHT AND LEFT HEAVY — character `┙` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+251A` BOX DRAWINGS UP HEAVY AND LEFT LIGHT — character `┚` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+251B` BOX DRAWINGS HEAVY UP AND LEFT — character `┛` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+251C` BOX DRAWINGS LIGHT VERTICAL AND RIGHT — character `├` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+251D` BOX DRAWINGS VERTICAL LIGHT AND RIGHT HEAVY — character `┝` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+251E` BOX DRAWINGS UP HEAVY AND RIGHT DOWN LIGHT — character `┞` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+251F` BOX DRAWINGS DOWN HEAVY AND RIGHT UP LIGHT — character `┟` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Unused cells: All sixteen cells are occupied.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep all black source ink well away from separators. For box-drawing and block-element profiles, exact Unicode edge placement is applied later as standard vector metric normalization; the generated raster must supply the original topology, line weights, fill pattern, and relative proportions. Use
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
