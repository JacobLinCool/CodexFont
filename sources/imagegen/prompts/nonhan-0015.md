# Image-generated non-Han sheet nonhan-0015

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0015.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P12-PUNC-CJK`
- Metric/design profiles: `cjk-wide, nonspacing-mark`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0015.png` (`13ff7d449f0046cbc56c5a3cb6f0c454a857c938c496254cd31223fb38c5fb52`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0015.png`, SHA-256 `13ff7d449f0046cbc56c5a3cb6f0c454a857c938c496254cd31223fb38c5fb52`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P12-PUNC-CJK`
Metric/design profiles present: `cjk-wide, nonspacing-mark`
- [cjk-wide] Compose the glyph for a full CJK em with the requested encoded orientation and punctuation position.
- [nonspacing-mark] Draw only the requested combining-mark ink, enlarged enough to identify in its cell; do not add a base, dotted circle, or carrier glyph.
- [nonspacing-mark] The final font metric is zero advance; the raster cell is an identity capture canvas, not evidence of final spacing.

Exact occupied cells:
- Cell 01: `U+3022` HANGZHOU NUMERAL TWO — character `〢` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 02: `U+3023` HANGZHOU NUMERAL THREE — character `〣` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 03: `U+3024` HANGZHOU NUMERAL FOUR — character `〤` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 04: `U+3025` HANGZHOU NUMERAL FIVE — character `〥` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 05: `U+3026` HANGZHOU NUMERAL SIX — character `〦` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 06: `U+3027` HANGZHOU NUMERAL SEVEN — character `〧` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 07: `U+3028` HANGZHOU NUMERAL EIGHT — character `〨` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 08: `U+3029` HANGZHOU NUMERAL NINE — character `〩` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 09: `U+302A` IDEOGRAPHIC LEVEL TONE MARK — character `〪` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-218"}`
- Cell 10: `U+302B` IDEOGRAPHIC RISING TONE MARK — character `〫` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-228"}`
- Cell 11: `U+302C` IDEOGRAPHIC DEPARTING TONE MARK — character `〬` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-232"}`
- Cell 12: `U+302D` IDEOGRAPHIC ENTERING TONE MARK — character `〭` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-222"}`
- Cell 13: `U+302E` HANGUL SINGLE DOT TONE MARK — character `〮` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 14: `U+302F` HANGUL DOUBLE DOT TONE MARK — character `〯` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 15: `U+3030` WAVY DASH — character `〰` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":1024},"side_bearings":{"left":32,"right":32}}`
- Cell 16: `U+3031` VERTICAL KANA REPEAT MARK — character `〱` — profile `cjk-wide` — metrics `{"horizontal_advance":{"kind":"fixed","value":1024},"vertical_advance":{"kind":"fixed","value":2048},"side_bearings":{"left":32,"right":32}}`

Unused cells: All sixteen cells are occupied.

Identity-critical anatomy:
- Cells 01–08 must follow the copybook shapes, not Western tally-mark
  interpretations of their English numeral names.
- Cell 01 is exactly two vertical strokes, the left shorter than the right.
  Cell 02 is exactly three vertical strokes, with the middle shortest and the
  right tallest.
- Cell 03 is exactly two crossing diagonal strokes forming `×`; it has no
  vertical stroke and no horizontal bar.
- Cell 04 is the distinctive connected copybook form with an upper fork and a
  rounded lower-right loop; it is not four bars crossed by a slash.
- Cell 05 is a bottom horizontal with one central vertical rising from it.
  Cell 06 adds one separate lower horizontal to the top horizontal-and-vertical
  construction. Cell 07 adds exactly two separate lower horizontals.
- Cell 08 is the distinctive connected copybook form with its compact upper
  junction and two diverging lower diagonals; it is not a grid, hash, or tally.
- Cells 09–12 are four separate small hollow circles whose cell-local
  positions are semantically distinct: lower-left, upper-left, upper-right,
  then lower-right. Preserve those four corner positions exactly; do not
  center or homogenize them.
- Cell 13 is one filled dot and Cell 14 is exactly two vertically stacked
  filled dots.
- Cell 16 is one tall left-pointing angle made from two joined diagonal
  strokes, visually like a narrow `<`; it is not two vertical bars.

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
