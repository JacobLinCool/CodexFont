# Image-generated Han-delta sheet dict-han-0073

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0073.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0073.png` (`21f6c7afa87c58ca6809d1579354da831eaeb86dbd0db31465b145afad478973`)
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
蜮蠨裒覯 / 趓踽蹅郾 / 鄘酮鉦銚 / 錡鎘鏦鏨.

Exact occupied cells:
- Cell 01: U+872E `蜮` CJK UNIFIED IDEOGRAPH-872E
- Cell 02: U+8828 `蠨` CJK UNIFIED IDEOGRAPH-8828
- Cell 03: U+88D2 `裒` CJK UNIFIED IDEOGRAPH-88D2
- Cell 04: U+89AF `覯` CJK UNIFIED IDEOGRAPH-89AF
- Cell 05: U+8D93 `趓` CJK UNIFIED IDEOGRAPH-8D93
- Cell 06: U+8E3D `踽` CJK UNIFIED IDEOGRAPH-8E3D
- Cell 07: U+8E45 `蹅` CJK UNIFIED IDEOGRAPH-8E45
- Cell 08: U+90FE `郾` CJK UNIFIED IDEOGRAPH-90FE
- Cell 09: U+9118 `鄘` CJK UNIFIED IDEOGRAPH-9118
- Cell 10: U+916E `酮` CJK UNIFIED IDEOGRAPH-916E
- Cell 11: U+9266 `鉦` CJK UNIFIED IDEOGRAPH-9266
- Cell 12: U+929A `銚` CJK UNIFIED IDEOGRAPH-929A
- Cell 13: U+9321 `錡` CJK UNIFIED IDEOGRAPH-9321
- Cell 14: U+9398 `鎘` CJK UNIFIED IDEOGRAPH-9398
- Cell 15: U+93E6 `鏦` CJK UNIFIED IDEOGRAPH-93E6
- Cell 16: U+93E8 `鏨` CJK UNIFIED IDEOGRAPH-93E8

Text (verbatim):
蜮蠨裒覯
趓踽蹅郾
鄘酮鉦銚
錡鎘鏦鏨

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
