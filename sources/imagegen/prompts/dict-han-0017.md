# Image-generated Han-delta sheet dict-han-0017

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0017.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0017.png` (`1ee4635da44cbff9ea5656d53b7372c1f4c6901a6d58ca5c5e49b000f744fca8`)
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
翊衿踅輅 / 幄撅椹槿 / 猗稗篦腴 / 芾茜蓍蓽.

Exact occupied cells:
- Cell 01: U+7FCA `翊` CJK UNIFIED IDEOGRAPH-7FCA
- Cell 02: U+887F `衿` CJK UNIFIED IDEOGRAPH-887F
- Cell 03: U+8E05 `踅` CJK UNIFIED IDEOGRAPH-8E05
- Cell 04: U+8F05 `輅` CJK UNIFIED IDEOGRAPH-8F05
- Cell 05: U+5E44 `幄` CJK UNIFIED IDEOGRAPH-5E44
- Cell 06: U+6485 `撅` CJK UNIFIED IDEOGRAPH-6485
- Cell 07: U+6939 `椹` CJK UNIFIED IDEOGRAPH-6939
- Cell 08: U+69FF `槿` CJK UNIFIED IDEOGRAPH-69FF
- Cell 09: U+7317 `猗` CJK UNIFIED IDEOGRAPH-7317
- Cell 10: U+7A17 `稗` CJK UNIFIED IDEOGRAPH-7A17
- Cell 11: U+7BE6 `篦` CJK UNIFIED IDEOGRAPH-7BE6
- Cell 12: U+8174 `腴` CJK UNIFIED IDEOGRAPH-8174
- Cell 13: U+82BE `芾` CJK UNIFIED IDEOGRAPH-82BE
- Cell 14: U+831C `茜` CJK UNIFIED IDEOGRAPH-831C
- Cell 15: U+84CD `蓍` CJK UNIFIED IDEOGRAPH-84CD
- Cell 16: U+84FD `蓽` CJK UNIFIED IDEOGRAPH-84FD

Text (verbatim):
翊衿踅輅
幄撅椹槿
猗稗篦腴
芾茜蓍蓽

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
