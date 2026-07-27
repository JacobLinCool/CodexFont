# Image-generated Han-delta sheet dict-han-0011

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0011.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0011.png` (`6514ac9fdc08f8f95bdc59c859340cedc1d8cf636d55a2035e6be661c6b2b4e7`)
- Copybook role: identity-reference-only-no-outline-import
- State: awaiting generation; all review gates pending

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for an original
Traditional Chinese handwriting font in the clear-hand-tc family

Input images:
1. Image 1 is STYLE ONLY. Match its fine black gel-pen weight, rounded
   terminals, natural right slant, optical scale, pure-white background, and
   faint 4×4 grid. Do not copy its characters or outlines.
2. Image 2 is IDENTITY REFERENCE ONLY. Use it to disambiguate the exact
   Unicode character assigned to each cell. Do not trace, reproduce, or import
   its printed outlines or gray grid geometry.

Primary request: write exactly 16 new isolated Traditional
Chinese glyphs in a strict four-by-four grid, in this exact row-major order:
譙邃旄椽 / 笄笏裱襃 / 謐迤陟儻 / 寰泠琨筲.

Exact occupied cells:
- Cell 01: U+8B59 `譙` CJK UNIFIED IDEOGRAPH-8B59
- Cell 02: U+9083 `邃` CJK UNIFIED IDEOGRAPH-9083
- Cell 03: U+65C4 `旄` CJK UNIFIED IDEOGRAPH-65C4
- Cell 04: U+693D `椽` CJK UNIFIED IDEOGRAPH-693D
- Cell 05: U+7B04 `笄` CJK UNIFIED IDEOGRAPH-7B04
- Cell 06: U+7B0F `笏` CJK UNIFIED IDEOGRAPH-7B0F
- Cell 07: U+88F1 `裱` CJK UNIFIED IDEOGRAPH-88F1
- Cell 08: U+8943 `襃` CJK UNIFIED IDEOGRAPH-8943
- Cell 09: U+8B10 `謐` CJK UNIFIED IDEOGRAPH-8B10
- Cell 10: U+8FE4 `迤` CJK UNIFIED IDEOGRAPH-8FE4
- Cell 11: U+965F `陟` CJK UNIFIED IDEOGRAPH-965F
- Cell 12: U+513B `儻` CJK UNIFIED IDEOGRAPH-513B
- Cell 13: U+5BF0 `寰` CJK UNIFIED IDEOGRAPH-5BF0
- Cell 14: U+6CE0 `泠` CJK UNIFIED IDEOGRAPH-6CE0
- Cell 15: U+7428 `琨` CJK UNIFIED IDEOGRAPH-7428
- Cell 16: U+7B72 `筲` CJK UNIFIED IDEOGRAPH-7B72

Text (verbatim):
譙邃旄椽
笄笏裱襃
謐迤陟儻
寰泠琨筲

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
