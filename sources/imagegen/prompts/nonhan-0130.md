# Image-generated non-Han sheet nonhan-0130

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0130.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P53-NUMBER-FORMS`
- Metric/design profiles: `proportional, fullwidth`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0130.png` (`f0098de76676cce026ac7879e612252ddd2786a5e65ed44baa409bb571b02f9a`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0130.png`, SHA-256 `f0098de76676cce026ac7879e612252ddd2786a5e65ed44baa409bb571b02f9a`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 5 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P53-NUMBER-FORMS`
Metric/design profiles present: `proportional, fullwidth`
- [proportional] Keep natural proportional side bearings and optical width; do not force the glyph into a fullwidth square.
- [fullwidth] Use the exact fullwidth identity and balanced full-em optical scale; do not substitute an ASCII or halfwidth compatibility character.

Exact occupied cells:
- Cell 01: `U+2180` ROMAN NUMERAL ONE THOUSAND C D — character `ↀ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 02: `U+2181` ROMAN NUMERAL FIVE THOUSAND — character `ↁ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 03: `U+2182` ROMAN NUMERAL TEN THOUSAND — character `ↂ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 04: `U+2183` ROMAN NUMERAL REVERSED ONE HUNDRED — character `Ↄ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 05: `U+2189` VULGAR FRACTION ZERO THIRDS — character `↉` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`

Critical topology corrections:
- Cell 01 U+2180 must have one completely closed outer oval enclosure with a
  central vertical divider joining its top and bottom. Do not leave the outer
  contour open and do not substitute a plain phi.
- Cell 02 U+2181 must retain both D-shaped structures shown in the copybook:
  one tall outer D enclosure and one smaller inner D bowl joined to the same
  left vertical stem. Never simplify it to a plain capital D.
- Cell 03 U+2182 must retain two nested closed oval enclosures, both crossed
  by the same central vertical stem. Never omit the smaller inner oval and
  never simplify it to Cell 01.
- Cell 05 U+2189 must use the copybook's diagonal vulgar-fraction layout:
  small zero at upper left, long rising slash through the center, and small
  three at lower right. Do not use a horizontal fraction bar or stack the
  zero directly above the three.

Unused cells: Cells 06–16 are intentionally unused and must remain completely blank.

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
