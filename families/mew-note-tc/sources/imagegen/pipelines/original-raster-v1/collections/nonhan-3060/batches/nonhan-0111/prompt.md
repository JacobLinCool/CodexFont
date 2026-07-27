# Mew Note TC original raster batch

Create one new lossless raster sheet for **mew-note-tc** batch
`nonhan-0111` in collection `nonhan-3060`.

Draw exactly 4 rows × 4 columns in row-major order on a
clean white background with black ink. Keep every glyph centered inside its
cell with generous clear padding. Do not draw grid lines, cell numbers,
captions, signatures, shadows, paper texture, or any extra marks.

Exact row-major characters:

ヰ ヱ ヲ ン
ヴ ヵ ヶ ヷ
ヸ ヹ ヺ ・
ー ヽ ヾ ヿ

Exact cell assignments:

- Cell 01: ヰ (U+30F0) — tail-terminal
- Cell 02: ヱ (U+30F1) — soft-terminal
- Cell 03: ヲ (U+30F2) — soft-terminal
- Cell 04: ン (U+30F3) — soft-terminal
- Cell 05: ヴ (U+30F4) — tail-terminal
- Cell 06: ヵ (U+30F5) — soft-terminal
- Cell 07: ヶ (U+30F6) — soft-terminal
- Cell 08: ヷ (U+30F7) — soft-terminal
- Cell 09: ヸ (U+30F8) — tail-terminal
- Cell 10: ヹ (U+30F9) — soft-terminal
- Cell 11: ヺ (U+30FA) — soft-terminal
- Cell 12: ・ (U+30FB) — soft-terminal
- Cell 13: ー (U+30FC) — tail-terminal
- Cell 14: ヽ (U+30FD) — soft-terminal
- Cell 15: ヾ (U+30FE) — soft-terminal
- Cell 16: ヿ (U+30FF) — soft-terminal

Use upright, rounded gel-pen handwriting with low contrast and soft, human
terminals. The result must remain readable at 16 px. Preserve every requested
character's exact identity and topology; never simplify, substitute, translate,
or normalize a character.

Only cells listed as `tail-terminal` may receive one restrained cat-tail curl.
The curl must continue an existing final stroke in the same connected contour,
stay inside the advance, and preserve identity. Tail cells: 1, 5, 9, 13.
Every other cell must use its declared `soft-terminal` or `neutral-safety`
class. Never add detached ears, hats, faces, whiskers, paws, silhouettes,
floating decoration, spikes, sharp thorns, self-intersections, or a second tail.

Reference roles:

- `mew-note-han-style-pilot-v2`: style-only-no-raster-or-outline-reuse (families/mew-note-tc/pilots/mew-note-han-v2-raster.png, SHA-256 b6ae4ac12a769e979b86df7af1a3d7f4a824ea79ba67bf7b43802c3fc49eff82)
- `mew-note-nonhan-style-pilot`: style-only-no-raster-or-outline-reuse (families/mew-note-tc/pilots/mew-note-nonhan-raster.png, SHA-256 eb755d5fb065798812ddc15619025ab79b290d06fc89626ba845b6580e882f41)

The identity copybook identifies code points only. Style-pilot images establish
stroke rhythm and the attached-tail idea only. Do not trace, transform, paste,
or reuse any reference outline or raster.

