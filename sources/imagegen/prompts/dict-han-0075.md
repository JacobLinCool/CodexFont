# Image-generated Han-delta sheet dict-han-0075

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0075.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0075.png` (`709d9d607daa1dfc3e9fce0d1b2da334a46d6d106eac84cfd4f52beeea89c207`)
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
啁喨嗛嘵 / 嚳孥尨峋 / 嶮巹徯惓 / 惛愒懌戩.

Exact occupied cells:
- Cell 01: U+5541 `啁` CJK UNIFIED IDEOGRAPH-5541
- Cell 02: U+55A8 `喨` CJK UNIFIED IDEOGRAPH-55A8
- Cell 03: U+55DB `嗛` CJK UNIFIED IDEOGRAPH-55DB
- Cell 04: U+5635 `嘵` CJK UNIFIED IDEOGRAPH-5635
- Cell 05: U+56B3 `嚳` CJK UNIFIED IDEOGRAPH-56B3
- Cell 06: U+5B65 `孥` CJK UNIFIED IDEOGRAPH-5B65
- Cell 07: U+5C28 `尨` CJK UNIFIED IDEOGRAPH-5C28
- Cell 08: U+5CCB `峋` CJK UNIFIED IDEOGRAPH-5CCB
- Cell 09: U+5DAE `嶮` CJK UNIFIED IDEOGRAPH-5DAE
- Cell 10: U+5DF9 `巹` CJK UNIFIED IDEOGRAPH-5DF9
- Cell 11: U+5FAF `徯` CJK UNIFIED IDEOGRAPH-5FAF
- Cell 12: U+60D3 `惓` CJK UNIFIED IDEOGRAPH-60D3
- Cell 13: U+60DB `惛` CJK UNIFIED IDEOGRAPH-60DB
- Cell 14: U+6112 `愒` CJK UNIFIED IDEOGRAPH-6112
- Cell 15: U+61CC `懌` CJK UNIFIED IDEOGRAPH-61CC
- Cell 16: U+6229 `戩` CJK UNIFIED IDEOGRAPH-6229

Text (verbatim):
啁喨嗛嘵
嚳孥尨峋
嶮巹徯惓
惛愒懌戩

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
