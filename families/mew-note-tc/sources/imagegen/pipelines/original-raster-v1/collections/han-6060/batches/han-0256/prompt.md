# Mew Note TC original raster batch

Create one new lossless raster sheet for **mew-note-tc** batch
`han-0256` in collection `han-6060`.

Draw exactly 4 rows × 4 columns in row-major order on a
clean white background with black ink. Keep every glyph centered inside its
cell with generous clear padding. Do not draw grid lines, cell numbers,
captions, signatures, shadows, paper texture, or any extra marks.

Exact row-major characters:

竺 竽 笆 笠
笙 笞 筐 筏
筷 箝 箔 箏
箴 篁 篙 簑

Exact cell assignments:

- Cell 01: 竺 (U+7AFA) — soft-terminal
- Cell 02: 竽 (U+7AFD) — tail-terminal
- Cell 03: 笆 (U+7B06) — soft-terminal
- Cell 04: 笠 (U+7B20) — soft-terminal
- Cell 05: 笙 (U+7B19) — soft-terminal
- Cell 06: 笞 (U+7B1E) — tail-terminal
- Cell 07: 筐 (U+7B50) — soft-terminal
- Cell 08: 筏 (U+7B4F) — soft-terminal
- Cell 09: 筷 (U+7B77) — soft-terminal
- Cell 10: 箝 (U+7B9D) — tail-terminal
- Cell 11: 箔 (U+7B94) — soft-terminal
- Cell 12: 箏 (U+7B8F) — soft-terminal
- Cell 13: 箴 (U+7BB4) — soft-terminal
- Cell 14: 篁 (U+7BC1) — tail-terminal
- Cell 15: 篙 (U+7BD9) — soft-terminal
- Cell 16: 簑 (U+7C11) — soft-terminal

Use upright, rounded gel-pen handwriting with low contrast and soft, human
terminals. The result must remain readable at 16 px. Preserve every requested
character's exact identity and topology; never simplify, substitute, translate,
or normalize a character.

Only cells listed as `tail-terminal` may receive one restrained cat-tail curl.
The curl must continue an existing final stroke in the same connected contour,
stay inside the advance, and preserve identity. Tail cells: 2, 6, 10, 14.
Every other cell must use its declared `soft-terminal` or `neutral-safety`
class. Never add detached ears, hats, faces, whiskers, paws, silhouettes,
floating decoration, spikes, sharp thorns, self-intersections, or a second tail.

Reference roles:

- `mew-note-han-style-pilot-v2`: style-only-no-raster-or-outline-reuse (families/mew-note-tc/pilots/mew-note-han-v2-raster.png, SHA-256 b6ae4ac12a769e979b86df7af1a3d7f4a824ea79ba67bf7b43802c3fc49eff82)

The identity copybook identifies code points only. Style-pilot images establish
stroke rhythm and the attached-tail idea only. Do not trace, transform, paste,
or reuse any reference outline or raster.

