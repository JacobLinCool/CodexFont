# Image-generated non-Han sheet nonhan-0033

- Descriptor schema: 2
- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/nonhan-0033.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Repertoire: `sources/imagegen/repertoires/nonhan-3060.json`
- Repertoire SHA-256: `42791eeb3981f04895529ad7770b00a86a815f9c4dffa16369df9f7ec1892ce4`
- Design group: `P16-MARK-COMBINING`
- Metric/design profiles: `nonspacing-mark`
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/nonhan-0033.png` (`cc882b09efb2cf9b201eeca5012daafa0544f1fc1d8f618849fa28b9337097e4`)
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
2. Image 2 (`sources/imagegen/copybooks/nonhan-0033.png`, SHA-256 `cc882b09efb2cf9b201eeca5012daafa0544f1fc1d8f618849fa28b9337097e4`) is IDENTITY
   REFERENCE ONLY. It uses neutral local print fonts to disambiguate the exact
   Unicode glyph in each corresponding cell. Do not trace, reproduce, or
   import its printed outlines. Do not reproduce its gray grid geometry.

Primary request: draw exactly 16 new isolated glyphs in a
strict four-by-four grid, in the exact row-major cell order below. Author each
glyph as original Clear Hand TC handwriting from a blank canvas.

Design group: `P16-MARK-COMBINING`
Metric/design profiles present: `nonspacing-mark`
- [nonspacing-mark] Draw only the requested combining-mark ink, enlarged enough to identify in its cell; do not add a base, dotted circle, or carrier glyph.
- [nonspacing-mark] The final font metric is zero advance; the raster cell is an identity capture canvas, not evidence of final spacing.

Exact occupied cells:
- Cell 01: `U+0351` COMBINING LEFT HALF RING ABOVE — character `͑` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 02: `U+0352` COMBINING FERMATA — character `͒` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 03: `U+0353` COMBINING X BELOW — character `͓` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 04: `U+0354` COMBINING LEFT ARROWHEAD BELOW — character `͔` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 05: `U+0355` COMBINING RIGHT ARROWHEAD BELOW — character `͕` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 06: `U+0356` COMBINING RIGHT ARROWHEAD AND UP ARROWHEAD BELOW — character `͖` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-220"}`
- Cell 07: `U+0357` COMBINING RIGHT HALF RING ABOVE — character `͗` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 08: `U+035D` COMBINING DOUBLE BREVE — character `͝` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-234"}`
- Cell 09: `U+035E` COMBINING DOUBLE MACRON — character `͞` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-234"}`
- Cell 10: `U+035F` COMBINING DOUBLE MACRON BELOW — character `͟` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-233"}`
- Cell 11: `U+0360` COMBINING DOUBLE TILDE — character `͠` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-234"}`
- Cell 12: `U+0361` COMBINING DOUBLE INVERTED BREVE — character `͡` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-234"}`
- Cell 13: `U+0362` COMBINING DOUBLE RIGHTWARDS ARROW BELOW — character `͢` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-233"}`
- Cell 14: `U+0363` COMBINING LATIN SMALL LETTER A — character `ͣ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 15: `U+0364` COMBINING LATIN SMALL LETTER E — character `ͤ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`
- Cell 16: `U+0365` COMBINING LATIN SMALL LETTER I — character `ͥ` — profile `nonspacing-mark` — metrics `{"horizontal_advance":{"kind":"fixed","value":0},"vertical_advance":{"kind":"fixed","value":0},"side_bearings":{"left":0,"right":0},"mark_class":"ccc-230"}`

Unused cells: All sixteen cells are occupied.

Identity-critical anatomy:
- Cell 01 is a `C`-shaped left half ring opening right; Cell 07 is its mirror,
  a right half ring opening left. Do not swap or close either ring.
- Cell 02 is one downward-opening fermata cap with exactly one detached filled
  dot centered below.
- Cell 06 contains exactly two adjacent components, one right arrowhead and one
  up arrowhead (`> ^`), not a fused zigzag.
- Cells 08–13 are spanning marks. Each cell contains exactly one continuous
  wide mark, never two duplicated halves: an upward-opening double breve, one
  long macron, one long macron below, one long tilde, one downward-opening
  inverted breve, then one long rightwards arrow.
- More literally, Cell 08 is one broad smooth `U`-shaped arc, never a `W` or
  two joined cups. Cells 09 and 10 each contain exactly one single horizontal
  stroke, never an equals sign. Cell 11 contains exactly one single wavy line,
  never two stacked waves. Cell 12 is one broad smooth downward-opening cap
  shaped like `∩`, never a `W`, cup, or two joined arcs.
- In the Unicode names for Cells 08–13, “DOUBLE” means that one mark spans two
  eventual base letters. It never means two visible marks in this identity
  sheet. Count the visible mark components before output: Cell 08 one arc,
  Cell 09 one line, Cell 10 one line, Cell 11 one wave, Cell 12 one cap, and
  Cell 13 one arrow.
- Cells 14–16 are the isolated small letters `a`, `e`, and dotted `i`.

Composition: square image; four equal rows and four equal columns; generous
outer margin; only faint thin light-gray straight separators; exactly one
centered black target glyph in every occupied cell. Keep all black ink well
away from separators. Use pure white with no texture, gradient, lighting, or
shadow.

Grid geometry is a hard machine-readability requirement:
- Draw one complete axis-aligned outer square and exactly three complete
  full-height interior vertical rules plus exactly three complete full-width
  interior horizontal rules.
- Place the interior rules at precisely 25%, 50%, and 75% of the outer
  square's inner width/height, producing four exactly equal columns and four
  exactly equal rows. Do not vary row or column spacing.
- Every rule must be perfectly straight, unbroken, parallel, constant-width
  light gray, and meet the outer square cleanly. No perspective, skew,
  curvature, offset segment, missing segment, fade, doubled rule, or extra
  line is allowed.

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
