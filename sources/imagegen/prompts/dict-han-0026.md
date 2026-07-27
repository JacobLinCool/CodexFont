# Image-generated Han-delta sheet dict-han-0026

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0026.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0026.png` (`783659608a566bb9d35d4190d7e60b7bed64a9305689ee07c58246cb8d92e571`)
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
傕噁塋婺 / 徂忑撣枳 / 殄殢殽眊 / 紓芡薺虢.

Exact occupied cells:
- Cell 01: U+5095 `傕` CJK UNIFIED IDEOGRAPH-5095
- Cell 02: U+5641 `噁` CJK UNIFIED IDEOGRAPH-5641
- Cell 03: U+584B `塋` CJK UNIFIED IDEOGRAPH-584B
- Cell 04: U+5A7A `婺` CJK UNIFIED IDEOGRAPH-5A7A
- Cell 05: U+5F82 `徂` CJK UNIFIED IDEOGRAPH-5F82
- Cell 06: U+5FD1 `忑` CJK UNIFIED IDEOGRAPH-5FD1
- Cell 07: U+64A3 `撣` CJK UNIFIED IDEOGRAPH-64A3
- Cell 08: U+67B3 `枳` CJK UNIFIED IDEOGRAPH-67B3
- Cell 09: U+6B84 `殄` CJK UNIFIED IDEOGRAPH-6B84
- Cell 10: U+6BA2 `殢` CJK UNIFIED IDEOGRAPH-6BA2
- Cell 11: U+6BBD `殽` CJK UNIFIED IDEOGRAPH-6BBD
- Cell 12: U+770A `眊` CJK UNIFIED IDEOGRAPH-770A
- Cell 13: U+7D13 `紓` CJK UNIFIED IDEOGRAPH-7D13
- Cell 14: U+82A1 `芡` CJK UNIFIED IDEOGRAPH-82A1
- Cell 15: U+85BA `薺` CJK UNIFIED IDEOGRAPH-85BA
- Cell 16: U+8662 `虢` CJK UNIFIED IDEOGRAPH-8662

Text (verbatim):
傕噁塋婺
徂忑撣枳
殄殢殽眊
紓芡薺虢

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
