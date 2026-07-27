# Image-generated Han-delta sheet dict-han-0027

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0027.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0027.png` (`aafecf49bf0fa1e51d3b7ae76f7b4f03773edd40b48837fb2e026cfb4b026fad`)
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
蛉蜚醯鐙 / 閫颭髫嶔 / 悛懆捋捽 / 撂旒旻昵.

Exact occupied cells:
- Cell 01: U+86C9 `蛉` CJK UNIFIED IDEOGRAPH-86C9
- Cell 02: U+871A `蜚` CJK UNIFIED IDEOGRAPH-871A
- Cell 03: U+91AF `醯` CJK UNIFIED IDEOGRAPH-91AF
- Cell 04: U+9419 `鐙` CJK UNIFIED IDEOGRAPH-9419
- Cell 05: U+95AB `閫` CJK UNIFIED IDEOGRAPH-95AB
- Cell 06: U+98AD `颭` CJK UNIFIED IDEOGRAPH-98AD
- Cell 07: U+9AEB `髫` CJK UNIFIED IDEOGRAPH-9AEB
- Cell 08: U+5D94 `嶔` CJK UNIFIED IDEOGRAPH-5D94
- Cell 09: U+609B `悛` CJK UNIFIED IDEOGRAPH-609B
- Cell 10: U+61C6 `懆` CJK UNIFIED IDEOGRAPH-61C6
- Cell 11: U+634B `捋` CJK UNIFIED IDEOGRAPH-634B
- Cell 12: U+637D `捽` CJK UNIFIED IDEOGRAPH-637D
- Cell 13: U+6482 `撂` CJK UNIFIED IDEOGRAPH-6482
- Cell 14: U+65D2 `旒` CJK UNIFIED IDEOGRAPH-65D2
- Cell 15: U+65FB `旻` CJK UNIFIED IDEOGRAPH-65FB
- Cell 16: U+6635 `昵` CJK UNIFIED IDEOGRAPH-6635

Text (verbatim):
蛉蜚醯鐙
閫颭髫嶔
悛懆捋捽
撂旒旻昵

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
