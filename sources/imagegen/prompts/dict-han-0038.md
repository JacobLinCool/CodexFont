# Image-generated Han-delta sheet dict-han-0038

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0038.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0038.png` (`7b5dd433f74289008506f3b3777bfce2ac86e8e9e86dec4ae2ed06d668d4b568`)
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
簟罍聵膂 / 詡謳蹧鈀 / 錂錮隰驤 / 髀鼉乜侔.

Exact occupied cells:
- Cell 01: U+7C1F `簟` CJK UNIFIED IDEOGRAPH-7C1F
- Cell 02: U+7F4D `罍` CJK UNIFIED IDEOGRAPH-7F4D
- Cell 03: U+8075 `聵` CJK UNIFIED IDEOGRAPH-8075
- Cell 04: U+8182 `膂` CJK UNIFIED IDEOGRAPH-8182
- Cell 05: U+8A61 `詡` CJK UNIFIED IDEOGRAPH-8A61
- Cell 06: U+8B33 `謳` CJK UNIFIED IDEOGRAPH-8B33
- Cell 07: U+8E67 `蹧` CJK UNIFIED IDEOGRAPH-8E67
- Cell 08: U+9200 `鈀` CJK UNIFIED IDEOGRAPH-9200
- Cell 09: U+9302 `錂` CJK UNIFIED IDEOGRAPH-9302
- Cell 10: U+932E `錮` CJK UNIFIED IDEOGRAPH-932E
- Cell 11: U+96B0 `隰` CJK UNIFIED IDEOGRAPH-96B0
- Cell 12: U+9A64 `驤` CJK UNIFIED IDEOGRAPH-9A64
- Cell 13: U+9AC0 `髀` CJK UNIFIED IDEOGRAPH-9AC0
- Cell 14: U+9F09 `鼉` CJK UNIFIED IDEOGRAPH-9F09
- Cell 15: U+4E5C `乜` CJK UNIFIED IDEOGRAPH-4E5C
- Cell 16: U+4F94 `侔` CJK UNIFIED IDEOGRAPH-4F94

Text (verbatim):
簟罍聵膂
詡謳蹧鈀
錂錮隰驤
髀鼉乜侔

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
