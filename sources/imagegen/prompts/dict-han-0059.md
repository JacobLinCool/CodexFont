# Image-generated Han-delta sheet dict-han-0059

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0059.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0059.png` (`8d50321aa7d49bbf3149ea63fd3d4b27cd772730ead1e5ef07a0d820767f481b`)
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
灝炤燁珽 / 瑒疔痧盅 / 眵睇砑箠 / 紞纊罏翥.

Exact occupied cells:
- Cell 01: U+705D `灝` CJK UNIFIED IDEOGRAPH-705D
- Cell 02: U+70A4 `炤` CJK UNIFIED IDEOGRAPH-70A4
- Cell 03: U+71C1 `燁` CJK UNIFIED IDEOGRAPH-71C1
- Cell 04: U+73FD `珽` CJK UNIFIED IDEOGRAPH-73FD
- Cell 05: U+7452 `瑒` CJK UNIFIED IDEOGRAPH-7452
- Cell 06: U+7594 `疔` CJK UNIFIED IDEOGRAPH-7594
- Cell 07: U+75E7 `痧` CJK UNIFIED IDEOGRAPH-75E7
- Cell 08: U+76C5 `盅` CJK UNIFIED IDEOGRAPH-76C5
- Cell 09: U+7735 `眵` CJK UNIFIED IDEOGRAPH-7735
- Cell 10: U+7747 `睇` CJK UNIFIED IDEOGRAPH-7747
- Cell 11: U+7811 `砑` CJK UNIFIED IDEOGRAPH-7811
- Cell 12: U+7BA0 `箠` CJK UNIFIED IDEOGRAPH-7BA0
- Cell 13: U+7D1E `紞` CJK UNIFIED IDEOGRAPH-7D1E
- Cell 14: U+7E8A `纊` CJK UNIFIED IDEOGRAPH-7E8A
- Cell 15: U+7F4F `罏` CJK UNIFIED IDEOGRAPH-7F4F
- Cell 16: U+7FE5 `翥` CJK UNIFIED IDEOGRAPH-7FE5

Text (verbatim):
灝炤燁珽
瑒疔痧盅
眵睇砑箠
紞纊罏翥

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
