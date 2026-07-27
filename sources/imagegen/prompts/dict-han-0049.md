# Image-generated Han-delta sheet dict-han-0049

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0049.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0049.png` (`35fd0164bde34585847d4b3414fca9b2bd3c3941773322fec60e81d8834ab911`)
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
玦璠瓴癟 / 砒磧礱祧 / 糝艫荃蕓 / 蝟襬賾跂.

Exact occupied cells:
- Cell 01: U+73A6 `玦` CJK UNIFIED IDEOGRAPH-73A6
- Cell 02: U+74A0 `璠` CJK UNIFIED IDEOGRAPH-74A0
- Cell 03: U+74F4 `瓴` CJK UNIFIED IDEOGRAPH-74F4
- Cell 04: U+765F `癟` CJK UNIFIED IDEOGRAPH-765F
- Cell 05: U+7812 `砒` CJK UNIFIED IDEOGRAPH-7812
- Cell 06: U+78E7 `磧` CJK UNIFIED IDEOGRAPH-78E7
- Cell 07: U+7931 `礱` CJK UNIFIED IDEOGRAPH-7931
- Cell 08: U+7967 `祧` CJK UNIFIED IDEOGRAPH-7967
- Cell 09: U+7CDD `糝` CJK UNIFIED IDEOGRAPH-7CDD
- Cell 10: U+826B `艫` CJK UNIFIED IDEOGRAPH-826B
- Cell 11: U+8343 `荃` CJK UNIFIED IDEOGRAPH-8343
- Cell 12: U+8553 `蕓` CJK UNIFIED IDEOGRAPH-8553
- Cell 13: U+875F `蝟` CJK UNIFIED IDEOGRAPH-875F
- Cell 14: U+896C `襬` CJK UNIFIED IDEOGRAPH-896C
- Cell 15: U+8CFE `賾` CJK UNIFIED IDEOGRAPH-8CFE
- Cell 16: U+8DC2 `跂` CJK UNIFIED IDEOGRAPH-8DC2

Text (verbatim):
玦璠瓴癟
砒磧礱祧
糝艫荃蕓
蝟襬賾跂

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
