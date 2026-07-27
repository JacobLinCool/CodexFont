# Image-generated non-Han sheet nonhan-0048

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0048.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P22-FULLWIDTH-SYMBOLS`
- Metric/design profiles: `fullwidth, halfwidth`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0048.png` (`d023ddc35590a48e8f1f0c656832f8b9ec3e5c64254677db1ef4470598ebc90d`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0048.png`, SHA-256 `d023ddc35590a48e8f1f0c656832f8b9ec3e5c64254677db1ef4470598ebc90d`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 14 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P22-FULLWIDTH-SYMBOLS`
Metric/design profiles present: `fullwidth, halfwidth`
- [fullwidth] Use the exact fullwidth identity and balanced full-em optical scale; do not substitute an ASCII or halfwidth compatibility character.
- [halfwidth] Use the compact halfwidth identity; do not substitute its fullwidth counterpart or stretch it to fill the cell.

Exact occupied cells:
- Cell 01: `U+FFE0` FULLWIDTH CENT SIGN — character `￠` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 02: `U+FFE1` FULLWIDTH POUND SIGN — character `￡` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 03: `U+FFE2` FULLWIDTH NOT SIGN — character `￢` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 04: `U+FFE3` FULLWIDTH MACRON — character `￣` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 05: `U+FFE4` FULLWIDTH BROKEN BAR — character `￤` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 06: `U+FFE5` FULLWIDTH YEN SIGN — character `￥` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 07: `U+FFE6` FULLWIDTH WON SIGN — character `￦` — profile `fullwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 08: `U+FFE8` HALFWIDTH FORMS LIGHT VERTICAL — character `￨` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 09: `U+FFE9` HALFWIDTH LEFTWARDS ARROW — character `￩` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 10: `U+FFEA` HALFWIDTH UPWARDS ARROW — character `￪` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 11: `U+FFEB` HALFWIDTH RIGHTWARDS ARROW — character `￫` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 12: `U+FFEC` HALFWIDTH DOWNWARDS ARROW — character `￬` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 13: `U+FFED` HALFWIDTH BLACK SQUARE — character `￭` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 14: `U+FFEE` HALFWIDTH WHITE CIRCLE — character `￮` — profile `halfwidth` — metrics `{"horizontal_advance":{"kind":"fixed","value":512},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`

Unused cells: Cells 15–16 are intentionally unused and must remain completely blank.

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
