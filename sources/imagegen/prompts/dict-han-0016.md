# Image-generated Han-delta sheet dict-han-0016

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0016.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0016.png` (`48a4816bf4308c38738cf87aec90d71f91c3eb38e70bde95137ffb2e2d71f4da`)
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
諢遶鉶鑪 / 鴈㑳亹哽 / 弋汎漉澠 / 濮煢獼瑾.

Exact occupied cells:
- Cell 01: U+8AE2 `諢` CJK UNIFIED IDEOGRAPH-8AE2
- Cell 02: U+9076 `遶` CJK UNIFIED IDEOGRAPH-9076
- Cell 03: U+9276 `鉶` CJK UNIFIED IDEOGRAPH-9276
- Cell 04: U+946A `鑪` CJK UNIFIED IDEOGRAPH-946A
- Cell 05: U+9D08 `鴈` CJK UNIFIED IDEOGRAPH-9D08
- Cell 06: U+3473 `㑳` CJK UNIFIED IDEOGRAPH-3473
- Cell 07: U+4EB9 `亹` CJK UNIFIED IDEOGRAPH-4EB9
- Cell 08: U+54FD `哽` CJK UNIFIED IDEOGRAPH-54FD
- Cell 09: U+5F0B `弋` CJK UNIFIED IDEOGRAPH-5F0B
- Cell 10: U+6C4E `汎` CJK UNIFIED IDEOGRAPH-6C4E
- Cell 11: U+6F09 `漉` CJK UNIFIED IDEOGRAPH-6F09
- Cell 12: U+6FA0 `澠` CJK UNIFIED IDEOGRAPH-6FA0
- Cell 13: U+6FEE `濮` CJK UNIFIED IDEOGRAPH-6FEE
- Cell 14: U+7162 `煢` CJK UNIFIED IDEOGRAPH-7162
- Cell 15: U+737C `獼` CJK UNIFIED IDEOGRAPH-737C
- Cell 16: U+747E `瑾` CJK UNIFIED IDEOGRAPH-747E

Text (verbatim):
諢遶鉶鑪
鴈㑳亹哽
弋汎漉澠
濮煢獼瑾

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
