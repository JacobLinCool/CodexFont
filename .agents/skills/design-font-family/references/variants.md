# Purpose-specific branches

## Monospace

- Declare one fixed horizontal advance for spacing glyphs.
- Include `iIl1|`, `O0`, paired punctuation, operators, box drawing, combining
  marks, tabs, and programming ligatures in the pilot.
- Validate terminal columns, repeated indentation, code blocks, and mixed CJK
  width policy.
- Do not call a family monospaced when wide-script or symbol exceptions are
  undeclared.

## UI and small text

- Prioritize open apertures, stable side bearings, distinct confusables, and
  low-size raster coverage.
- Add dense labels, disabled states, numerals, localization strings, and
  high-contrast themes to the proof set.

## Display

- Define the minimum intended size and permit details that would fail text-size
  gates only when the contract makes that boundary explicit.
- Test repeated headlines, punctuation rhythm, and extreme letter pairs.

## Accessibility

- Specify confusable pairs and minimum distinguishability criteria.
- Test low-resolution, low-contrast, zoom, dyslexia-relevant forms, and assistive
  rendering environments appropriate to the use case.

## Vertical or East Asian layout

- Freeze unencoded alternates separately from encoded repertoire.
- Validate `vert`/`vrt2` substitutions and placed bounds with a production
  shaper.
- Preserve authored placement while applying the declared advance policy.

## Symbols and technical fonts

- Use standards to verify identity and topology, not to import outlines.
- Test fill state, edge contact, symmetry, fractions, extensible pieces, and
  semantic alignment as explicit glyph classes.
