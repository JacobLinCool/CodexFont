# Mew Note TC Han style pilot v2

This file records the exact two image-generation prompts used for the v2
pilot. The second call edits only the digit-zero cell. Neither result counts
toward encoded coverage.

## Generation

- Generator: built-in `image_gen`
- Call: `exec-29882601-d6c0-44c5-861a-dcc73bc8885b`
- Result SHA-256: `bb5c9b7e0220feb45c7190871f9d99b85937f24df9470a29d3f688b87cd47c15`
- Style reference: `mew-note-han-raster.png`
  (`9cce5322a07df04f6e4c0e90e4f98fac020d18fb6994dc5be28e38c8c73182e4`)
- Han identity copybook: `mew-note-han-copybook.png`
  (`0fa1995e5555fe70c878a70379250935565a943de41696a0e8555e85436bd4ba`)
- Confusable-form copybook: `mew-note-nonhan-copybook.png`
  (`e845e50c5b6cbb6a02e585e243b53a1c69363354dcb60748f67d8208d7edb510`)

```text
Create a NEW replacement style pilot from a blank canvas for the original Mew Note TC handwriting family. Do not edit or copy any earlier glyph outline.

Image 1 is style-only: use its clean rounded black monoline gel-pen feeling.
Image 2 is the exact cell-by-cell identity copybook for the requested 4×4 order.
Image 3 is an identity reference for confusable non-Han forms; use its SLASHED ZERO design as the required digit-zero identity.
All references are evidence only. Redraw every glyph independently.

Exact row-major cells:
01 永 — neutral soft terminals, NO tail.
02 貓 — ONE small connected cat-tail curl on an identity-safe final stroke.
03 手 — neutral soft terminals, NO tail.
04 寫 — ONE small connected cat-tail curl on an identity-safe final stroke.
05 龍 — neutral soft terminals, NO tail.
06 鬱 — neutral soft terminals, NO tail. This is the critical correction: draw the complete standard Traditional 鬱 topology with all semantic components and strokes, matching Image 2 exactly; enlarge it within the cell, use fine even monoline strokes, generous internal gaps, open counters, and no decorative curl so the structure remains recognizable at 16 px. Never simplify it to 郁 or another variant.
07 國 — neutral soft terminals, NO tail.
08 愛 — ONE small connected cat-tail curl on an identity-safe final stroke.
09 A — neutral soft terminals, NO tail.
10 a — ONE small connected cat-tail curl on its existing final stroke.
11 G — neutral soft terminals, NO tail.
12 g — ONE small connected cat-tail curl on its existing descender terminal.
13 0 — SLASHED ZERO exactly like the slashed-zero identity in Image 3; a closed oval with one clean diagonal slash, NO tail, NO Q-like spur, and clearly distinct from uppercase O and Q.
14 8 — neutral soft terminals, NO tail.
15 あ — neutral soft terminals, NO tail.
16 ア — neutral soft terminals, NO tail.

Exactly cells 02, 04, 08, 10, and 12 have one attached tail. No other cell may contain any curl, spiral, looped terminal, Q-like spur, cat motif, or decorative hook.

Composition: high-resolution square; strict four-by-four grid with five faint thin neutral-gray straight rules in each direction; pure white background; generous padding; exactly one centered black glyph per cell. Preserve Taiwan Traditional Chinese, Latin, numeral, hiragana, and katakana identities. Fine rounded monoline, controlled handwriting, open counters, readable at small sizes.

No detached contours, cat ears, hats, faces, paws, whiskers, floating marks, labels, captions, codepoints, watermark, texture, shadow, brush effects, extra or missing strokes, simplified variants, spikes, thorns, self-intersections, cropped ink, duplicate glyphs, or reordered cells.
```

## Zero correction

- Generator: built-in `image_gen`
- Call: `exec-a37b11cd-92cb-4449-9ed3-4d3c0ea5124e`
- Parent result SHA-256:
  `bb5c9b7e0220feb45c7190871f9d99b85937f24df9470a29d3f688b87cd47c15`
- Identity reference: `mew-note-nonhan-raster.png`
  (`eb755d5fb065798812ddc15619025ab79b290d06fc89626ba845b6580e882f41`)
- Final raster: `mew-note-han-v2-raster.png`
  (`b6ae4ac12a769e979b86df7af1a3d7f4a824ea79ba67bf7b43802c3fc49eff82`)

```text
Edit Image 1 only to correct Cell 13, the bottom-left cell. Preserve all other fifteen cells pixel-for-pixel in identity, stroke structure, style, tail assignment, scale, placement, grid, and background.

Cell 13 must be the same handwritten SLASHED DIGIT ZERO design shown in Image 2, row 2 cell 3: a closed oval digit 0 containing one clean diagonal slash that stays inside the oval and meets the oval boundary cleanly. The slash must NOT protrude outside the oval. It must have NO Q-like spur, NO tail curl, and must remain distinct from uppercase O, Q, empty-set ∅, and Latin Ø.

Do not change 鬱 or any other glyph. Do not add or remove any tails outside Cell 13. No labels, extra marks, texture, shadows, spikes, clipping, or reordered cells.
```
