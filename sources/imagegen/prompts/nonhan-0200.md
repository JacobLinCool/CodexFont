# Image-generated non-Han sheet nonhan-0200

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0200.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P62-BOX-DRAWING`
- Metric/design profiles: `box-drawing`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0200.png` (`2f7e8b2ac3de961abe22f76a4674100f7c8c193bd1ddb278a13a4e6d4b1edc74`)
- Copybook role: identity-reference-only-no-outline-import
- State: awaiting generation; all review gates pending

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original non-Han
glyphs in the Clear Hand TC family

CRITICAL production geometry: this is a connecting-tile source, not a centered
glyph specimen. The finished sheet must visibly contain every required single
or double line crossing the faint cell rules. A sheet of floating symbols
surrounded by white margins is categorically wrong and must not be returned.

Input images:
1. Image 1 (`sources/imagegen/raster/common-0001.png`, SHA-256 `2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`) is STYLE ONLY.
   Match its fine black gel-pen weight, rounded terminals, natural but
   controlled handwriting rhythm, optical scale, pure-white background, and
   faint 4×4 grid. Do not copy its Han characters.
2. Image 2 (`sources/imagegen/copybooks/nonhan-0200.png`, SHA-256 `2f7e8b2ac3de961abe22f76a4674100f7c8c193bd1ddb278a13a4e6d4b1edc74`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Read only its topology and
   single/double line assignment. Its large white margins and short centered
   arm lengths are explicitly WRONG for this production sheet. Do not trace,
   reproduce, or import its printed outlines or gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P62-BOX-DRAWING`
Metric/design profiles present: `box-drawing`
- [box-drawing] Preserve every endpoint, junction, single/double line, and weight distinction exactly; connection topology outranks decorative variation.

Exact occupied cells:
- Cell 01: `U+2550` BOX DRAWINGS DOUBLE HORIZONTAL — character `═` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 02: `U+2551` BOX DRAWINGS DOUBLE VERTICAL — character `║` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 03: `U+2552` BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE — character `╒` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 04: `U+2553` BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE — character `╓` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 05: `U+2554` BOX DRAWINGS DOUBLE DOWN AND RIGHT — character `╔` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 06: `U+2555` BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE — character `╕` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 07: `U+2556` BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE — character `╖` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 08: `U+2557` BOX DRAWINGS DOUBLE DOWN AND LEFT — character `╗` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 09: `U+2558` BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE — character `╘` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 10: `U+2559` BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE — character `╙` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 11: `U+255A` BOX DRAWINGS DOUBLE UP AND RIGHT — character `╚` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 12: `U+255B` BOX DRAWINGS UP SINGLE AND LEFT DOUBLE — character `╛` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 13: `U+255C` BOX DRAWINGS UP DOUBLE AND LEFT SINGLE — character `╜` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 14: `U+255D` BOX DRAWINGS DOUBLE UP AND LEFT — character `╝` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 15: `U+255E` BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE — character `╞` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`
- Cell 16: `U+255F` BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE — character `╟` — profile `box-drawing` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":0,"right":0}}`

Box-drawing edge-contact requirements:
- These are CONNECTING tiles. Each named directional arm must run from its
  junction continuously to the matching boundary of its own cell: UP touches
  the top edge, DOWN the bottom edge, LEFT the left edge, and RIGHT the right
  edge. Do not draw short floating centered lines or corners.
- Cell 01 contacts LEFT and RIGHT. Cell 02 contacts TOP and BOTTOM. Cells
  03–05 contact BOTTOM and RIGHT. Cells 06–08 contact BOTTOM and LEFT. Cells
  09–11 contact TOP and RIGHT. Cells 12–14 contact TOP and LEFT. Cells 15–16
  contact TOP, BOTTOM, and RIGHT.
- SINGLE means exactly one black stroke along that named direction. DOUBLE
  means exactly two parallel black strokes separated by a clean, continuous
  white gap; DOUBLE never means one heavy stroke. Preserve the copybook's
  exact single-to-double or double-to-single corner/junction construction.
- Both parallel strokes of every DOUBLE continuation reach the matching edge.
  A SINGLE continuation reaches its edge once. Do not merge a double pair
  into one thick line or invent a third line.
- Exact arm map, where `1`=SINGLE and `2`=DOUBLE; directions not listed are
  absent: C01 L:2 R:2; C02 U:2 D:2; C03 D:1 R:2; C04 D:2 R:1;
  C05 D:2 R:2; C06 D:1 L:2; C07 D:2 L:1; C08 D:2 L:2;
  C09 U:1 R:2; C10 U:2 R:1; C11 U:2 R:2; C12 U:1 L:2;
  C13 U:2 L:1; C14 U:2 L:2; C15 U:1 D:1 R:2; C16 U:2 D:2 R:1.
- Mandatory cell-local construction: treat every cell as its own coordinate
  viewport with x=0% at LEFT, x=100% at RIGHT, y=0% at TOP, and
  y=100% at BOTTOM. Put each corner or junction near (50%,50%). Draw every
  named arm to construction coordinate -25% or 125%; this deliberate
  geometric overextension compensates the generator's strong optical inset.
  Do not clip or stop it at the separator: every required single or double
  black line must cover the faint gray rule and remain visible for about 2–3%
  beyond its centerline. This short authorized overshoot belongs to the
  originating connector and is not an unintended bridge. Never use the
  copybook's centered length or margins. White edge clearance is an automatic
  rejection.
- Hard gate: every cell has exactly the named directional continuations and
  line multiplicities. Any extra arm, missing arm, single/double swap,
  collapsed white gap, or endpoint clearance is categorically wrong.

Unused cells: All sixteen cells are occupied.

Composition: square image; four equal rows and four equal columns; only faint
thin light-gray straight separators; exactly one black target glyph in every
occupied cell. This box-drawing sheet is an explicit exception to ordinary
centering and separator clearance: extend every named continuation arm to its
required cell boundary. Keep all other ink inside its assigned cell. Use pure
white with no texture, gradient, lighting, or shadow.

Final 16-cell boundary audit before output: for every direction in the exact
arm map, zoom in and verify that every required single or double black line
covers the separator centerline and remains visible 2–3% beyond it. If any
named line still has white clearance, extend it and recheck. Do not return a
centered draft.

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
