# Image-generated Han-delta sheet dict-han-0045

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0045.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0045.png` (`bd0c05fbba3f4e9c44c3f0e78d21aa31b12076030fffef73ec97d088a02bf957`)
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
鏇闍隗鵰 / 唏噲嬈嶙 / 恚掾搆搧 / 攄昕晻栝.

Exact occupied cells:
- Cell 01: U+93C7 `鏇` CJK UNIFIED IDEOGRAPH-93C7
- Cell 02: U+95CD `闍` CJK UNIFIED IDEOGRAPH-95CD
- Cell 03: U+9697 `隗` CJK UNIFIED IDEOGRAPH-9697
- Cell 04: U+9D70 `鵰` CJK UNIFIED IDEOGRAPH-9D70
- Cell 05: U+550F `唏` CJK UNIFIED IDEOGRAPH-550F
- Cell 06: U+5672 `噲` CJK UNIFIED IDEOGRAPH-5672
- Cell 07: U+5B08 `嬈` CJK UNIFIED IDEOGRAPH-5B08
- Cell 08: U+5D99 `嶙` CJK UNIFIED IDEOGRAPH-5D99
- Cell 09: U+605A `恚` CJK UNIFIED IDEOGRAPH-605A
- Cell 10: U+63BE `掾` CJK UNIFIED IDEOGRAPH-63BE
- Cell 11: U+6406 `搆` CJK UNIFIED IDEOGRAPH-6406
- Cell 12: U+6427 `搧` CJK UNIFIED IDEOGRAPH-6427
- Cell 13: U+6504 `攄` CJK UNIFIED IDEOGRAPH-6504
- Cell 14: U+6615 `昕` CJK UNIFIED IDEOGRAPH-6615
- Cell 15: U+667B `晻` CJK UNIFIED IDEOGRAPH-667B
- Cell 16: U+681D `栝` CJK UNIFIED IDEOGRAPH-681D

Text (verbatim):
鏇闍隗鵰
唏噲嬈嶙
恚掾搆搧
攄昕晻栝

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
