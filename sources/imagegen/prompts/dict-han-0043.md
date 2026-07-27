# Image-generated Han-delta sheet dict-han-0043

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0043.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0043.png` (`e45610ee51c2bf95d6710218a3edbbd7a639a551c255c9f06c837582db964c8f`)
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
悃扑扦槎 / 汩汶湄瀲 / 燋瓘疣痾 / 矻祓秕箇.

Exact occupied cells:
- Cell 01: U+6083 `悃` CJK UNIFIED IDEOGRAPH-6083
- Cell 02: U+6251 `扑` CJK UNIFIED IDEOGRAPH-6251
- Cell 03: U+6266 `扦` CJK UNIFIED IDEOGRAPH-6266
- Cell 04: U+69CE `槎` CJK UNIFIED IDEOGRAPH-69CE
- Cell 05: U+6C69 `汩` CJK UNIFIED IDEOGRAPH-6C69
- Cell 06: U+6C76 `汶` CJK UNIFIED IDEOGRAPH-6C76
- Cell 07: U+6E44 `湄` CJK UNIFIED IDEOGRAPH-6E44
- Cell 08: U+7032 `瀲` CJK UNIFIED IDEOGRAPH-7032
- Cell 09: U+71CB `燋` CJK UNIFIED IDEOGRAPH-71CB
- Cell 10: U+74D8 `瓘` CJK UNIFIED IDEOGRAPH-74D8
- Cell 11: U+75A3 `疣` CJK UNIFIED IDEOGRAPH-75A3
- Cell 12: U+75FE `痾` CJK UNIFIED IDEOGRAPH-75FE
- Cell 13: U+77FB `矻` CJK UNIFIED IDEOGRAPH-77FB
- Cell 14: U+7953 `祓` CJK UNIFIED IDEOGRAPH-7953
- Cell 15: U+79D5 `秕` CJK UNIFIED IDEOGRAPH-79D5
- Cell 16: U+7B87 `箇` CJK UNIFIED IDEOGRAPH-7B87

Text (verbatim):
悃扑扦槎
汩汶湄瀲
燋瓘疣痾
矻祓秕箇

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
