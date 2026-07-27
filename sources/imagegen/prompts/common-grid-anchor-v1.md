# Common-Han imagegen grid prompt, anchor v1

This is the canonical prompt template used after the first style sheet. The
immutable PNG is the actual glyph source; this template records the generation
contract and is not treated as a reproducible random seed.

```text
Use case: logo-brand
Asset type: high-resolution raster master sheet for an original Traditional
Chinese handwriting font

Input images: Image 1 is a style reference only. Match its exact fine black
gel-pen weight, rounded terminals, natural right slant, optical scale, spacing,
pure white background, and faint 4x4 grid. Do not copy its characters.

Primary request: Write exactly {character_count} new isolated Traditional
Chinese glyphs in a strict 4 by 4 grid, in this exact row-major order:
{row_text}.

Style/medium: careful Taiwanese adult handwriting, warm, refined and personal,
but instantly legible at small size; standard Taiwan Traditional Chinese
character topology; no cursive shorthand.

Text (verbatim): {verbatim_rows}.

Constraints: reproduce every requested character exactly once and in order;
Taiwan Traditional forms only; all complete standard strokes; one centered
black glyph per occupied cell; open counters; no extra marks, cropping, or
connected cells. Any unused trailing cells must remain completely blank.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, spikes,
thorn-like protrusions, accidental hooks, tangled cursive, signature, logo,
watermark.
```
