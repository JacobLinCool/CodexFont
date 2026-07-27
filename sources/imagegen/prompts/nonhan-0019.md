# Image-generated non-Han sheet nonhan-0019

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0019.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P13-PUNC-GENERAL`
- Metric/design profiles: `proportional, fullwidth`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0019.png` (`ffda55c45e297fb15b7017c8979e7e3a9f616a0b4517d4b7e87eadf911ce0767`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0019.png`, SHA-256 `ffda55c45e297fb15b7017c8979e7e3a9f616a0b4517d4b7e87eadf911ce0767`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P13-PUNC-GENERAL`
Metric/design profiles present: `proportional, fullwidth`
- [proportional] Keep natural proportional side bearings and optical width; do not force the glyph into a fullwidth square.
- [fullwidth] Use the exact fullwidth identity and balanced full-em optical scale; do not substitute an ASCII or halfwidth compatibility character.

Exact occupied cells:
- Cell 01: `U+2038` CARET — character `‸` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 02: `U+2039` SINGLE LEFT-POINTING ANGLE QUOTATION MARK — character `‹` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 03: `U+203A` SINGLE RIGHT-POINTING ANGLE QUOTATION MARK — character `›` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 04: `U+203B` REFERENCE MARK — character `※` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 05: `U+203C` DOUBLE EXCLAMATION MARK — character `‼` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 06: `U+203D` INTERROBANG — character `‽` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 07: `U+203E` OVERLINE — character `‾` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 08: `U+203F` UNDERTIE — character `‿` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 09: `U+2040` CHARACTER TIE — character `⁀` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 10: `U+2041` CARET INSERTION POINT — character `⁁` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 11: `U+2042` ASTERISM — character `⁂` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 12: `U+2043` HYPHEN BULLET — character `⁃` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 13: `U+2044` FRACTION SLASH — character `⁄` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 14: `U+2045` LEFT SQUARE BRACKET WITH QUILL — character `⁅` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 15: `U+2046` RIGHT SQUARE BRACKET WITH QUILL — character `⁆` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 16: `U+2047` DOUBLE QUESTION MARK — character `⁇` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`

Unused cells: All sixteen cells are occupied.

Identity-critical anatomy:
- Cell 04 is one diagonal `×` with exactly four detached solid black filled
  dots at its top, left, right, and bottom. All four dots must be filled disks,
  never hollow circles or rings.
- Cell 06 is a single fused interrobang: the question-mark bowl and the
  exclamation stem share one central construction above one dot. Never draw
  separate side-by-side `?` and `!` glyphs.
- For Cell 06, use one shared central descending stem, with the question bowl
  flowing into it through a broad rounded tangent join. Do not draw two
  near-parallel stems, a narrow wedge/gap between stems, an acute `V`, an
  inward cusp, a pointed notch, overlapping duplicate strokes, or any tiny
  hook/thorn. Every outer and inner turn must be visibly smooth and rounded,
  with rounded terminals suitable for clean vectorization.
- Cell 06's bowl-to-stem junction must be a visibly filleted rounded `Y`
  junction, not a diagonal stroke ending against a vertical stroke. Let the
  bowl approach and merge tangentially into the shared stem over a smooth
  curve. There must be no crossing, corner, sharp intersection, acute interior
  angle, or sudden width change anywhere at that junction.
- Cell 10 is the exact three-branch lambda-like insertion mark shown in the
  copybook: one long diagonal runs continuously from lower-left through the
  junction to upper-right, and a second diagonal branches from that junction
  down-right. It is not a simple `^`, `v`, `m`, `w`, or double peak. It has no
  dot, period, or detached component below it.
- Cell 10 must visibly have exactly three outer endpoints—lower-left,
  upper-right, and lower-right—and one interior branch junction. The junction
  must sit below the upper-right endpoint; it must not collapse onto the top
  endpoint. A two-endpoint caret is an identity failure.
- Cell 12 is one short thick horizontal hyphen bullet, not a normal long
  hyphen and not a dot.
- Cells 14 and 15 are quill brackets, not ordinary square brackets. Each has
  the copybook's extra short horizontal quill projecting inward from the
  middle of the vertical stem, in addition to its top and bottom feet.

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
