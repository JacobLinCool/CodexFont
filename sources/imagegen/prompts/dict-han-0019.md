# Image-generated Han-delta sheet dict-han-0019

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0019.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0019.png` (`5ac9b59ff21308cde2690e8e9006997f1377f25ebb031316460064986027f795`)
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
溟籀緋肐 / 裾讜踉踊 / 蹀頦僂愍 / 捺漭璨癰.

Exact occupied cells:
- Cell 01: U+6E9F `溟` CJK UNIFIED IDEOGRAPH-6E9F
- Cell 02: U+7C40 `籀` CJK UNIFIED IDEOGRAPH-7C40
- Cell 03: U+7DCB `緋` CJK UNIFIED IDEOGRAPH-7DCB
- Cell 04: U+8090 `肐` CJK UNIFIED IDEOGRAPH-8090
- Cell 05: U+88FE `裾` CJK UNIFIED IDEOGRAPH-88FE
- Cell 06: U+8B9C `讜` CJK UNIFIED IDEOGRAPH-8B9C
- Cell 07: U+8E09 `踉` CJK UNIFIED IDEOGRAPH-8E09
- Cell 08: U+8E0A `踊` CJK UNIFIED IDEOGRAPH-8E0A
- Cell 09: U+8E40 `蹀` CJK UNIFIED IDEOGRAPH-8E40
- Cell 10: U+9826 `頦` CJK UNIFIED IDEOGRAPH-9826
- Cell 11: U+50C2 `僂` CJK UNIFIED IDEOGRAPH-50C2
- Cell 12: U+610D `愍` CJK UNIFIED IDEOGRAPH-610D
- Cell 13: U+637A `捺` CJK UNIFIED IDEOGRAPH-637A
- Cell 14: U+6F2D `漭` CJK UNIFIED IDEOGRAPH-6F2D
- Cell 15: U+74A8 `璨` CJK UNIFIED IDEOGRAPH-74A8
- Cell 16: U+7670 `癰` CJK UNIFIED IDEOGRAPH-7670

Text (verbatim):
溟籀緋肐
裾讜踉踊
蹀頦僂愍
捺漭璨癰

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
