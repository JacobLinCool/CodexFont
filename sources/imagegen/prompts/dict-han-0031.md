# Image-generated Han-delta sheet dict-han-0031

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0031.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0031.png` (`6426afe591b67dd11b4adcaa65ebe0566aff0b4428a8f095cedb960dc8a88edd`)
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
擐旰晞枘 / 涌琮盱窣 / 竦綹繒腌 / 苻葳蓊蚍.

Exact occupied cells:
- Cell 01: U+64D0 `擐` CJK UNIFIED IDEOGRAPH-64D0
- Cell 02: U+65F0 `旰` CJK UNIFIED IDEOGRAPH-65F0
- Cell 03: U+665E `晞` CJK UNIFIED IDEOGRAPH-665E
- Cell 04: U+6798 `枘` CJK UNIFIED IDEOGRAPH-6798
- Cell 05: U+6D8C `涌` CJK UNIFIED IDEOGRAPH-6D8C
- Cell 06: U+742E `琮` CJK UNIFIED IDEOGRAPH-742E
- Cell 07: U+76F1 `盱` CJK UNIFIED IDEOGRAPH-76F1
- Cell 08: U+7AA3 `窣` CJK UNIFIED IDEOGRAPH-7AA3
- Cell 09: U+7AE6 `竦` CJK UNIFIED IDEOGRAPH-7AE6
- Cell 10: U+7DB9 `綹` CJK UNIFIED IDEOGRAPH-7DB9
- Cell 11: U+7E52 `繒` CJK UNIFIED IDEOGRAPH-7E52
- Cell 12: U+814C `腌` CJK UNIFIED IDEOGRAPH-814C
- Cell 13: U+82FB `苻` CJK UNIFIED IDEOGRAPH-82FB
- Cell 14: U+8473 `葳` CJK UNIFIED IDEOGRAPH-8473
- Cell 15: U+84CA `蓊` CJK UNIFIED IDEOGRAPH-84CA
- Cell 16: U+868D `蚍` CJK UNIFIED IDEOGRAPH-868D

Text (verbatim):
擐旰晞枘
涌琮盱窣
竦綹繒腌
苻葳蓊蚍

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
