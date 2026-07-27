# Image-generated Han-delta sheet dict-han-0069

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0069.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0069.png` (`e3f165f78b13c3948b10da0d02d8f10f1420fe802a35edaaeb5873bb2c8e2a6a`)
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
趼躞郴鄆 / 醱醲鎞陔 / 霢靉馘鶡 / 黹丱佹俶.

Exact occupied cells:
- Cell 01: U+8DBC `趼` CJK UNIFIED IDEOGRAPH-8DBC
- Cell 02: U+8E9E `躞` CJK UNIFIED IDEOGRAPH-8E9E
- Cell 03: U+90F4 `郴` CJK UNIFIED IDEOGRAPH-90F4
- Cell 04: U+9106 `鄆` CJK UNIFIED IDEOGRAPH-9106
- Cell 05: U+91B1 `醱` CJK UNIFIED IDEOGRAPH-91B1
- Cell 06: U+91B2 `醲` CJK UNIFIED IDEOGRAPH-91B2
- Cell 07: U+939E `鎞` CJK UNIFIED IDEOGRAPH-939E
- Cell 08: U+9654 `陔` CJK UNIFIED IDEOGRAPH-9654
- Cell 09: U+9722 `霢` CJK UNIFIED IDEOGRAPH-9722
- Cell 10: U+9749 `靉` CJK UNIFIED IDEOGRAPH-9749
- Cell 11: U+9998 `馘` CJK UNIFIED IDEOGRAPH-9998
- Cell 12: U+9DA1 `鶡` CJK UNIFIED IDEOGRAPH-9DA1
- Cell 13: U+9EF9 `黹` CJK UNIFIED IDEOGRAPH-9EF9
- Cell 14: U+4E31 `丱` CJK UNIFIED IDEOGRAPH-4E31
- Cell 15: U+4F79 `佹` CJK UNIFIED IDEOGRAPH-4F79
- Cell 16: U+4FF6 `俶` CJK UNIFIED IDEOGRAPH-4FF6

Text (verbatim):
趼躞郴鄆
醱醲鎞陔
霢靉馘鶡
黹丱佹俶

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
