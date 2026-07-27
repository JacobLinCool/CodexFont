# Image-generated non-Han sheet nonhan-0198

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0198.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P62-BOX-DRAWING`
- Metric/design profiles: `box-drawing`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0198.png` (`68ed1217711a1347c871201a2e879dd45314eea653fc5f40a0425c4f7eec9269`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0198.png`, SHA-256 `68ed1217711a1347c871201a2e879dd45314eea653fc5f40a0425c4f7eec9269`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Read its topology and light/heavy
   assignment; its exact printed proportions are non-binding. Do not trace,
   reproduce, or import its printed outlines or gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P62-BOX-DRAWING`
Metric/design profiles present: `box-drawing`
- [box-drawing] Preserve every endpoint, junction, single/double line, and weight distinction exactly; connection topology outranks decorative variation.

Exact occupied cells:
- Cell 01: `U+2530` BOX DRAWINGS DOWN HEAVY AND HORIZONTAL LIGHT — character `┰` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2531` BOX DRAWINGS RIGHT LIGHT AND LEFT DOWN HEAVY — character `┱` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2532` BOX DRAWINGS LEFT LIGHT AND RIGHT DOWN HEAVY — character `┲` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2533` BOX DRAWINGS HEAVY DOWN AND HORIZONTAL — character `┳` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2534` BOX DRAWINGS LIGHT UP AND HORIZONTAL — character `┴` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2535` BOX DRAWINGS LEFT HEAVY AND RIGHT UP LIGHT — character `┵` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2536` BOX DRAWINGS RIGHT HEAVY AND LEFT UP LIGHT — character `┶` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2537` BOX DRAWINGS UP LIGHT AND HORIZONTAL HEAVY — character `┷` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2538` BOX DRAWINGS UP HEAVY AND HORIZONTAL LIGHT — character `┸` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2539` BOX DRAWINGS RIGHT LIGHT AND LEFT UP HEAVY — character `┹` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+253A` BOX DRAWINGS LEFT LIGHT AND RIGHT UP HEAVY — character `┺` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+253B` BOX DRAWINGS HEAVY UP AND HORIZONTAL — character `┻` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+253C` BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL — character `┼` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+253D` BOX DRAWINGS LEFT HEAVY AND RIGHT VERTICAL LIGHT — character `┽` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+253E` BOX DRAWINGS RIGHT HEAVY AND LEFT VERTICAL LIGHT — character `┾` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+253F` BOX DRAWINGS VERTICAL LIGHT AND HORIZONTAL HEAVY — character `┿` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Identity-critical arm requirements:
- Raster endpoint position is not identity evidence; the v3 font pipeline
  performs standard box-drawing em-boundary normalization downstream.
  Prioritize the authored directions, arm count, junction topology, and
  light/heavy contrast. Centered source arms are acceptable.
- LIGHT means one narrow stroke and HEAVY means one visibly wider stroke;
  HEAVY never means two parallel strokes. Preserve the named weight of each
  individual arm through the junction. Use the identity copybook to resolve
  every asymmetric light/heavy junction.
- Exact arm map, where L=LIGHT and H=HEAVY; directions not listed are absent:
  C01 L:L R:L D:H; C02 L:H R:L D:H; C03 L:L R:H D:H; C04 L:H R:H D:H;
  C05 L:L R:L U:L; C06 L:H R:L U:L; C07 L:L R:H U:L; C08 L:H R:H U:L;
  C09 L:L R:L U:H; C10 L:H R:L U:H; C11 L:L R:H U:H; C12 L:H R:H U:H;
  C13 U:L D:L L:L R:L; C14 U:L D:L L:H R:L;
  C15 U:L D:L L:L R:H; C16 U:L D:L L:H R:H.
- Dominant correction: C02 must have HEAVY left and down arms but a LIGHT
  right arm. C03 must have LIGHT left but HEAVY right and down arms. Do not
  flatten either horizontal bar to one uniform weight.
- Hard gate: cells 01–12 have exactly their three listed arms; cells 13–16
  have exactly four. Any extra arm, missing arm, or swapped light/heavy
  assignment is categorically wrong.

Unused cells: All sixteen cells are occupied.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep black ink away from
separators. Use pure white with no texture, gradient, lighting, or shadow.

Constraints: preserve every requested Unicode identity, direction, topology,
dot, line count, enclosure, fill state, and paired distinction; output each
target exactly once and only in its assigned cell; keep the style handwritten
and legible at small text sizes. The identity copybook is evidence, never an
outline source.

Do not include any U+XXXX label, Unicode name, cell number, caption, legend,
dotted-circle carrier, annotation, signature, logo, or watermark. Do not
render anything in unused cells. Avoid typeset appearance, brush blobs, dry
brush, ink splatter, sharp miter spikes, thorn-like protrusions, accidental
canvas clipping, duplicate glyphs, missing glyphs, reordered cells, or
cross-cell stray ink.
```
