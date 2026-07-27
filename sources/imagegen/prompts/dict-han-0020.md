# Image-generated Han-delta sheet dict-han-0020

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0020.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0020.png` (`4f83046503d0a7087e0e1a2a7c608be495df0311fe86e773f239ac2f73dcb502`)
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
筮紬軫迓 / 鴇鼐囿嬛 / 徠斝棱櫟 / 滎熒羆蘅.

Exact occupied cells:
- Cell 01: U+7B6E `筮` CJK UNIFIED IDEOGRAPH-7B6E
- Cell 02: U+7D2C `紬` CJK UNIFIED IDEOGRAPH-7D2C
- Cell 03: U+8EEB `軫` CJK UNIFIED IDEOGRAPH-8EEB
- Cell 04: U+8FD3 `迓` CJK UNIFIED IDEOGRAPH-8FD3
- Cell 05: U+9D07 `鴇` CJK UNIFIED IDEOGRAPH-9D07
- Cell 06: U+9F10 `鼐` CJK UNIFIED IDEOGRAPH-9F10
- Cell 07: U+56FF `囿` CJK UNIFIED IDEOGRAPH-56FF
- Cell 08: U+5B1B `嬛` CJK UNIFIED IDEOGRAPH-5B1B
- Cell 09: U+5FA0 `徠` CJK UNIFIED IDEOGRAPH-5FA0
- Cell 10: U+659D `斝` CJK UNIFIED IDEOGRAPH-659D
- Cell 11: U+68F1 `棱` CJK UNIFIED IDEOGRAPH-68F1
- Cell 12: U+6ADF `櫟` CJK UNIFIED IDEOGRAPH-6ADF
- Cell 13: U+6ECE `滎` CJK UNIFIED IDEOGRAPH-6ECE
- Cell 14: U+7192 `熒` CJK UNIFIED IDEOGRAPH-7192
- Cell 15: U+7F86 `羆` CJK UNIFIED IDEOGRAPH-7F86
- Cell 16: U+8605 `蘅` CJK UNIFIED IDEOGRAPH-8605

Text (verbatim):
筮紬軫迓
鴇鼐囿嬛
徠斝棱櫟
滎熒羆蘅

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
