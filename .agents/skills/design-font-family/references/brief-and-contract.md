# Brief and design contract

## Turn feelings into decisions

Translate subjective input into observable constraints:

| Brief language | Contract questions |
|---|---|
| Friendly | Are joins round, apertures open, and terminals soft? |
| Technical | Are widths systematic, symbols distinguishable, and figures stable? |
| Handwritten | Which irregularities are intentional, and what remains aligned? |
| Quiet | What contrast, density, spacing, and terminal energy express restraint? |
| Monospaced | What is the fixed advance, and how are marks and wide scripts handled? |
| Compact | At which sizes must counters and neighboring strokes remain separate? |

Do not accept adjectives as validation criteria. Attach each adjective to
representative glyphs, words, sizes, or measurements.

## Required brief decisions

- Family and style names; initial release version.
- Intended environments, sizes, readers, languages, and directions.
- Personality keywords and explicit non-goals.
- Repertoire denominator, ordering authority, normalization, and exclusions.
- Stroke, contrast, slant, proportion, width, metrics, and spacing models.
- Required OpenType features and vertical or alternate forms.
- Identity references and their strictly non-outline role.
- Source and release licenses.
- Raster, geometry, proof, review, reproducibility, and browser gates.

## Pilot selection

Use a pilot large enough to expose the design system but small enough to revise.
Include:

- sparse and dense glyphs;
- horizontal, vertical, curved, and diagonal structures;
- open and enclosed counters;
- ascenders, descenders, overshoots, and marks;
- repeated stems and collision-prone pairs;
- punctuation, numerals, and symbols;
- each supported script's characteristic structures;
- special-purpose cases such as ambiguous programming characters.

Do not scale until the pilot passes at the intended sizes.

## Versioning

Use `1.000` for the first public font release and `1.0.0` for the surrounding
software package. Increment only after defining whether a change affects
outlines, metrics, mappings, features, metadata, or evidence.
