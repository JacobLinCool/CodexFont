# Image-generated Han-delta sheet dict-han-0063

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0063.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0063.png` (`47896b3ea2b3fc2891fafa5a06260744c39f0c4cfa4e1aa8303fdd82c5526b58`)
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
瀼煇璀町 / 畹痠瘖瞋 / 窳竑笵籽 / 紘緗縕聃.

Exact occupied cells:
- Cell 01: U+703C `瀼` CJK UNIFIED IDEOGRAPH-703C
- Cell 02: U+7147 `煇` CJK UNIFIED IDEOGRAPH-7147
- Cell 03: U+7480 `璀` CJK UNIFIED IDEOGRAPH-7480
- Cell 04: U+753A `町` CJK UNIFIED IDEOGRAPH-753A
- Cell 05: U+7579 `畹` CJK UNIFIED IDEOGRAPH-7579
- Cell 06: U+75E0 `痠` CJK UNIFIED IDEOGRAPH-75E0
- Cell 07: U+7616 `瘖` CJK UNIFIED IDEOGRAPH-7616
- Cell 08: U+778B `瞋` CJK UNIFIED IDEOGRAPH-778B
- Cell 09: U+7AB3 `窳` CJK UNIFIED IDEOGRAPH-7AB3
- Cell 10: U+7AD1 `竑` CJK UNIFIED IDEOGRAPH-7AD1
- Cell 11: U+7B35 `笵` CJK UNIFIED IDEOGRAPH-7B35
- Cell 12: U+7C7D `籽` CJK UNIFIED IDEOGRAPH-7C7D
- Cell 13: U+7D18 `紘` CJK UNIFIED IDEOGRAPH-7D18
- Cell 14: U+7DD7 `緗` CJK UNIFIED IDEOGRAPH-7DD7
- Cell 15: U+7E15 `縕` CJK UNIFIED IDEOGRAPH-7E15
- Cell 16: U+8043 `聃` CJK UNIFIED IDEOGRAPH-8043

Text (verbatim):
瀼煇璀町
畹痠瘖瞋
窳竑笵籽
紘緗縕聃

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
