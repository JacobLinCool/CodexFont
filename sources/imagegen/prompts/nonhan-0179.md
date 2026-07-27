# Image-generated non-Han sheet nonhan-0179

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0179.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P60-MISC-TECHNICAL`
- Metric/design profiles: `proportional`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0179.png` (`249fa6f4fcd8869cbfed7f8d955898ae522069ab7cac1d7a6e660847b249eee0`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0179.png`, SHA-256 `249fa6f4fcd8869cbfed7f8d955898ae522069ab7cac1d7a6e660847b249eee0`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P60-MISC-TECHNICAL`
Metric/design profiles present: `proportional`
- [proportional] Keep natural proportional side bearings and optical width; do not force the glyph into a fullwidth square.

Exact occupied cells:
- Cell 01: `U+2380` INSERTION SYMBOL — character `⎀` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 02: `U+2381` CONTINUOUS UNDERLINE SYMBOL — character `⎁` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 03: `U+2382` DISCONTINUOUS UNDERLINE SYMBOL — character `⎂` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 04: `U+2383` EMPHASIS SYMBOL — character `⎃` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 05: `U+2384` COMPOSITION SYMBOL — character `⎄` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 06: `U+2385` WHITE SQUARE WITH CENTRE VERTICAL LINE — character `⎅` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 07: `U+2386` ENTER SYMBOL — character `⎆` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 08: `U+2387` ALTERNATIVE KEY SYMBOL — character `⎇` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 09: `U+2388` HELM SYMBOL — character `⎈` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 10: `U+2389` CIRCLED HORIZONTAL BAR WITH NOTCH — character `⎉` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 11: `U+238A` CIRCLED TRIANGLE DOWN — character `⎊` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 12: `U+238B` BROKEN CIRCLE WITH NORTHWEST ARROW — character `⎋` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 13: `U+238C` UNDO SYMBOL — character `⎌` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 14: `U+238D` MONOSTABLE SYMBOL — character `⎍` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 15: `U+238E` HYSTERESIS SYMBOL — character `⎎` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`
- Cell 16: `U+238F` OPEN-CIRCUIT-OUTPUT H-TYPE SYMBOL — character `⎏` — profile `proportional` — metrics `{"horizontal_advance":{"kind":"source-proportional"},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":48,"right":48}}`

Identity corrections from rejected attempt:
- Cell 02 must contain one lowercase `a` followed by exactly three solid
  continuation dots, with one continuous underline spanning the entire
  `a...` sequence. Do not omit the three dots.
- Cell 03 must contain exactly two lowercase `a` glyphs side by side, with one
  separate underline segment beneath each `a`. Do not collapse it to one
  letter.
- Cell 07 must be the complete ENTER SYMBOL: a hollow right-pointing arrow
  enters from the left and sits inside a larger hollow diamond outline. The
  diamond is open only where the arrow shaft enters; retain both the inner
  arrowhead and the outer diamond point.
- Cell 09 is a circle crossed by exactly three full diameters (six spokes):
  one vertical diameter plus two diagonal diameters forming an X. There is NO
  horizontal diameter. All six outer stroke ends are plain rounded terminals;
  add no endpoint dots.
- Cell 11 must contain a completely SOLID-BLACK filled downward-pointing
  triangle centered inside the outlined circle. The triangle is not hollow or
  outlined.

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
