# Image-generated Han-delta sheet dict-han-0022

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0022.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0022.png` (`3eeaf5d182072f438ef7478ee93d2a1358d9b7f74f1b5331db581fa4c65d5c60`)
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
摭殞泮漚 / 潯礴糲芷 / 苫蒯蕤薈 / 薹蹻郝鍼.

Exact occupied cells:
- Cell 01: U+646D `摭` CJK UNIFIED IDEOGRAPH-646D
- Cell 02: U+6B9E `殞` CJK UNIFIED IDEOGRAPH-6B9E
- Cell 03: U+6CEE `泮` CJK UNIFIED IDEOGRAPH-6CEE
- Cell 04: U+6F1A `漚` CJK UNIFIED IDEOGRAPH-6F1A
- Cell 05: U+6F6F `潯` CJK UNIFIED IDEOGRAPH-6F6F
- Cell 06: U+7934 `礴` CJK UNIFIED IDEOGRAPH-7934
- Cell 07: U+7CF2 `糲` CJK UNIFIED IDEOGRAPH-7CF2
- Cell 08: U+82B7 `芷` CJK UNIFIED IDEOGRAPH-82B7
- Cell 09: U+82EB `苫` CJK UNIFIED IDEOGRAPH-82EB
- Cell 10: U+84AF `蒯` CJK UNIFIED IDEOGRAPH-84AF
- Cell 11: U+8564 `蕤` CJK UNIFIED IDEOGRAPH-8564
- Cell 12: U+8588 `薈` CJK UNIFIED IDEOGRAPH-8588
- Cell 13: U+85B9 `薹` CJK UNIFIED IDEOGRAPH-85B9
- Cell 14: U+8E7B `蹻` CJK UNIFIED IDEOGRAPH-8E7B
- Cell 15: U+90DD `郝` CJK UNIFIED IDEOGRAPH-90DD
- Cell 16: U+937C `鍼` CJK UNIFIED IDEOGRAPH-937C

Text (verbatim):
摭殞泮漚
潯礴糲芷
苫蒯蕤薈
薹蹻郝鍼

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
