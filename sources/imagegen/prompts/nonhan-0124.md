# Image-generated non-Han sheet nonhan-0124

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0124.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P52-LETTERLIKE`
- Metric/design profiles: `proportional, fullwidth`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0124.png` (`4ad87eb96281fd973dca80997dd79fab8a86bfaf2ed98569b4e64177eb6511b7`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0124.png`, SHA-256 `4ad87eb96281fd973dca80997dd79fab8a86bfaf2ed98569b4e64177eb6511b7`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P52-LETTERLIKE`
Metric/design profiles present: `proportional, fullwidth`
- [proportional] Keep natural proportional side bearings and optical width; do not force the glyph into a fullwidth square.
- [fullwidth] Use the exact fullwidth identity and balanced full-em optical scale; do not substitute an ASCII or halfwidth compatibility character.

Exact occupied cells:
- Cell 01: `U+2120` SERVICE MARK — character `℠` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 02: `U+2121` TELEPHONE SIGN — character `℡` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 03: `U+2122` TRADE MARK SIGN — character `™` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 04: `U+2123` VERSICLE — character `℣` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 05: `U+2124` DOUBLE-STRUCK CAPITAL Z — character `ℤ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 06: `U+2125` OUNCE SIGN — character `℥` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 07: `U+2126` OHM SIGN — character `Ω` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 08: `U+2127` INVERTED OHM SIGN — character `℧` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 09: `U+2128` BLACK-LETTER CAPITAL Z — character `ℨ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 10: `U+2129` TURNED GREEK SMALL LETTER IOTA — character `℩` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 11: `U+212A` KELVIN SIGN — character `K` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 12: `U+212B` ANGSTROM SIGN — character `Å` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 13: `U+212C` SCRIPT CAPITAL B — character `ℬ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 14: `U+212D` BLACK-LETTER CAPITAL C — character `ℭ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 15: `U+212E` ESTIMATED SYMBOL — character `℮` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 16: `U+212F` SCRIPT SMALL E — character `ℯ` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`

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
