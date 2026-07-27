# Image-generated non-Han sheet nonhan-0202

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0202.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P62-BOX-DRAWING`
- Metric/design profiles: `box-drawing`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0202.png` (`d7d89198c410839dd88b3f1f987de5d028c92ddfca79e99010f59e9c0cf991de`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0202.png`, SHA-256 `d7d89198c410839dd88b3f1f987de5d028c92ddfca79e99010f59e9c0cf991de`) is IDENTITY
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
- Cell 01: `U+2570` BOX DRAWINGS LIGHT ARC UP AND RIGHT — character `╰` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2571` BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT — character `╱` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2572` BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT — character `╲` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2573` BOX DRAWINGS LIGHT DIAGONAL CROSS — character `╳` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2574` BOX DRAWINGS LIGHT LEFT — character `╴` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2575` BOX DRAWINGS LIGHT UP — character `╵` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2576` BOX DRAWINGS LIGHT RIGHT — character `╶` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2577` BOX DRAWINGS LIGHT DOWN — character `╷` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2578` BOX DRAWINGS HEAVY LEFT — character `╸` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2579` BOX DRAWINGS HEAVY UP — character `╹` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+257A` BOX DRAWINGS HEAVY RIGHT — character `╺` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+257B` BOX DRAWINGS HEAVY DOWN — character `╻` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+257C` BOX DRAWINGS LIGHT LEFT AND HEAVY RIGHT — character `╼` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+257D` BOX DRAWINGS LIGHT UP AND HEAVY DOWN — character `╽` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+257E` BOX DRAWINGS HEAVY LEFT AND LIGHT RIGHT — character `╾` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+257F` BOX DRAWINGS HEAVY UP AND LIGHT DOWN — character `╿` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Box-drawing topology requirements:
- Cell 01's arc encodes UP and RIGHT. Cells 02–04 preserve the exact slash,
  backslash, or crossed-pair topology.
- Cells 05–12 are eight isolated single-arm marks, never opposing full spans.
  Cells 05/09 are horizontal LEFT arms; Cells 06/10 are vertical UP arms;
  Cells 07/11 are horizontal RIGHT arms; Cells 08/12 are vertical DOWN arms.
  Preserve the light/heavy distinction and the authored rounded terminal
  morphology. The Unicode name supplies the functional arm direction.
- A source mark may be optically centered, and antialiased ink may cross the
  geometric cell midpoint. Its absolute raster bounding box is segmentation
  and layout evidence, not Unicode identity and not a release metric. Do not
  reject or relabel a single arm solely from its source-side bbox.
- Cells 13/15 encode LEFT-to-RIGHT spans with their requested light/heavy
  halves. Cells 14/16 encode UP-to-DOWN spans with their requested light/heavy
  halves. The weight changes only at the exact center junction, with zero
  white seam; every glyph must remain exactly one connected component.
- All Cells 01–16 must each contain exactly one black connected component.
  In particular, the light and heavy halves in Cells 13–16 must overlap
  cleanly at the center rather than merely touch across an antialiased gap.
- The raster supplies original topology, weights, and junction quality.
  Standard v3 vector metric normalization uses `_edge_target_bounds` to map
  every Unicode-required arm to its exact named half-em and em boundary.

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
