# Image-generated non-Han sheet nonhan-0204

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0204.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P63-BLOCK-ELEMENTS`
- Metric/design profiles: `block-element`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0204.png` (`480d54a7dba79047aa5404d303083f42f8e5d5f8c509a5914431389018b565b5`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0204.png`, SHA-256 `480d54a7dba79047aa5404d303083f42f8e5d5f8c509a5914431389018b565b5`) is IDENTITY
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
- Cell 01: `U+2590` RIGHT HALF BLOCK — character `▐` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2591` LIGHT SHADE — character `░` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2592` MEDIUM SHADE — character `▒` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2593` DARK SHADE — character `▓` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2594` UPPER ONE EIGHTH BLOCK — character `▔` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2595` RIGHT ONE EIGHTH BLOCK — character `▕` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2596` QUADRANT LOWER LEFT — character `▖` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2597` QUADRANT LOWER RIGHT — character `▗` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2598` QUADRANT UPPER LEFT — character `▘` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2599` QUADRANT UPPER LEFT AND LOWER LEFT AND LOWER RIGHT — character `▙` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+259A` QUADRANT UPPER LEFT AND LOWER RIGHT — character `▚` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+259B` QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER LEFT — character `▛` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+259C` QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER RIGHT — character `▜` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+259D` QUADRANT UPPER RIGHT — character `▝` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+259E` QUADRANT UPPER RIGHT AND LOWER LEFT — character `▞` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+259F` QUADRANT UPPER RIGHT AND LOWER LEFT AND LOWER RIGHT — character `▟` — profile `block-element` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Block-element boundary, density, and quadrant requirements:
- These are functional patterns built within one consistent inset source box.
  Use exact axis-aligned half/eighth boundaries and square corners, and keep
  all source ink safely clear of the gray grid.
- Cell 01 fills the exact RIGHT half of its source box. Cells 02–04 are LIGHT,
  MEDIUM, and DARK shade over identical source boxes: use evenly distributed
  small discrete black marks at clearly increasing approximate 25%/50%/75%
  densities. Construct DARK as a black field with regular small white holes
  occupying about 25%, not as another 50% checkerboard. Do not substitute a
  solid rectangle, gray wash, gradient, or identical density.
- Cell 05 fills the exact UPPER 1/8 and Cell 06 the exact RIGHT 1/8 of the same
  common source-box dimensions.
- Cells 07–16 divide the common source box into four exact quadrants and fill
  only the quadrants named in each Unicode identity: 07 lower-left; 08
  lower-right; 09 upper-left; 10 upper-left + lower-left + lower-right; 11
  upper-left + lower-right; 12 upper-left + upper-right + lower-left; 13
  upper-left + upper-right + lower-right; 14 upper-right; 15 upper-right +
  lower-left; 16 upper-right + lower-left + lower-right. Adjacent filled
  quadrants join as one seamless polygon with no outline or white center seam;
  unlisted quadrants remain pure white. Thus Cells 10, 12, 13, and 16 each
  have exactly one connected solid component. In diagonal Cells 11 and 15,
  the two opposite filled quadrants must meet at exactly their shared center
  corner: no white gap and no overlap beyond that point. Under the pipeline's
  8-connected raster convention each diagonal pair is therefore one source
  component, and tracing must preserve one vector outer contour.
- The raster supplies original fill/shade topology, density ordering, and
  relative fractions. Standard v3 vector metric normalization later maps
  Unicode-required bounds to exact em edges. Hard gate: no rounded corners
  and no swapped or missing quadrant.

Unused cells: All sixteen cells are occupied.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep all black source ink
well away from separators. Exact Unicode edge placement is applied later as
standard vector metric normalization; the raster must supply the original
fill/shade topology, density ordering, and relative proportions. Use pure
white with no texture, gradient, lighting, or shadow.

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

## Hash-pinned correction generation

The first generated raster was rejected after an independent topology audit:
U+259A contained two source components but its vector build contained one
outer contour. Its complete rejected evidence is preserved under
`sources/imagegen/rejected/provenance/nonhan-0204-component-collapse-20260726/`.

The accepted candidate was produced by editing that rejected raster
(`3425e87997d516a0c722da78cd9f3232293cf079b1d38b6d7f6c7be30fd1672a`)
with built-in `image_gen` call `call_uPACzF1WXV0RJlhVX3fjSSFQ`. The exact
correction prompt was:

```text
Edit this original 4×4 font-source raster sheet. Preserve every pixel and
every glyph except Cell 11 (row 3, column 3), U+259A QUADRANT UPPER LEFT AND
LOWER RIGHT. In Cell 11 only, redraw the same two solid black diagonal
quadrants so the upper-left square and lower-right square meet cleanly at
exactly one central corner with no white gap and no overlap beyond that single
corner. They must form one 8-connected black source component at the center
while still visibly remaining the two requested opposite quadrants. Keep their
outer sizes, square axis-aligned edges, pure black fill, and the existing
grid/margins. Do not change Cell 15 or any shade/block glyph. No labels,
guides, added marks, blur, rounded corners, spikes, texture, shadow, or grid
changes.
```
