# Original raster authoring

## Batch contract

Each visible batch must pin:

- canonical batch ID and exact ordered glyph records;
- repertoire file and sequence hash;
- prompt and generator call;
- raw lossless raster and hash;
- grid dimensions, cell order, padding, and empty cells;
- identity copybook and style reference when used;
- pending review state that generation cannot self-approve.

Keep batches small enough that a reviewer can inspect every glyph. A 4×4 sheet
is a useful default, not a universal requirement.

## Prompt structure

State:

1. the medium and visual direction;
2. exact row-major glyph sequence;
3. background, ink polarity, grid, padding, and resolution;
4. stroke weight, contrast, terminal, slant, proportion, and spacing intent;
5. forbidden additions, substitutions, labels, decoration, shadows, and grid
   contact;
6. the role of any identity or style reference.

Do not ask the image model to invent glyph identity. The frozen repertoire is
authoritative.

## Reference boundary

References may answer “which character or feeling is intended?” They must not
answer “which outline should be copied?” Preserve rendered copybooks separately
from the original raster and label them
`identity-reference-only-no-outline-import`.

## Regeneration

Archive or delete rejected attempts according to the repository policy. Never
replace the canonical source in place while an approval still points to it.
After any correction, rebuild proofs and create a fresh hash chain.
