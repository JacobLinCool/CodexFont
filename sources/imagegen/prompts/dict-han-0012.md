# Image-generated Han-delta sheet dict-han-0012

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0012.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0012.png` (`34915b53864acd5967117a2539b7b678291c027a373ddf144b3d427b07658d31`)
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
纍衲蹌鐫 / 佺晷琦篋 / 苕茨蘧倞 / 垛屨彀蟄.

Exact occupied cells:
- Cell 01: U+7E8D `纍` CJK UNIFIED IDEOGRAPH-7E8D
- Cell 02: U+8872 `衲` CJK UNIFIED IDEOGRAPH-8872
- Cell 03: U+8E4C `蹌` CJK UNIFIED IDEOGRAPH-8E4C
- Cell 04: U+942B `鐫` CJK UNIFIED IDEOGRAPH-942B
- Cell 05: U+4F7A `佺` CJK UNIFIED IDEOGRAPH-4F7A
- Cell 06: U+6677 `晷` CJK UNIFIED IDEOGRAPH-6677
- Cell 07: U+7426 `琦` CJK UNIFIED IDEOGRAPH-7426
- Cell 08: U+7BCB `篋` CJK UNIFIED IDEOGRAPH-7BCB
- Cell 09: U+82D5 `苕` CJK UNIFIED IDEOGRAPH-82D5
- Cell 10: U+8328 `茨` CJK UNIFIED IDEOGRAPH-8328
- Cell 11: U+8627 `蘧` CJK UNIFIED IDEOGRAPH-8627
- Cell 12: U+501E `倞` CJK UNIFIED IDEOGRAPH-501E
- Cell 13: U+579B `垛` CJK UNIFIED IDEOGRAPH-579B
- Cell 14: U+5C68 `屨` CJK UNIFIED IDEOGRAPH-5C68
- Cell 15: U+5F40 `彀` CJK UNIFIED IDEOGRAPH-5F40
- Cell 16: U+87C4 `蟄` CJK UNIFIED IDEOGRAPH-87C4

Text (verbatim):
纍衲蹌鐫
佺晷琦篋
苕茨蘧倞
垛屨彀蟄

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
