# Image-generated Han-delta sheet dict-han-0021

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0021.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0021.png` (`b0a8af962c78423c0741b15d22b9eb1358c407b585c8b28c366622ec3ee0a506`)
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
虺跖酶醴 / 閬倈哏徼 / 樗檣罅翮 / 蓑觚跤嬭.

Exact occupied cells:
- Cell 01: U+867A `虺` CJK UNIFIED IDEOGRAPH-867A
- Cell 02: U+8DD6 `跖` CJK UNIFIED IDEOGRAPH-8DD6
- Cell 03: U+9176 `酶` CJK UNIFIED IDEOGRAPH-9176
- Cell 04: U+91B4 `醴` CJK UNIFIED IDEOGRAPH-91B4
- Cell 05: U+95AC `閬` CJK UNIFIED IDEOGRAPH-95AC
- Cell 06: U+5008 `倈` CJK UNIFIED IDEOGRAPH-5008
- Cell 07: U+54CF `哏` CJK UNIFIED IDEOGRAPH-54CF
- Cell 08: U+5FBC `徼` CJK UNIFIED IDEOGRAPH-5FBC
- Cell 09: U+6A17 `樗` CJK UNIFIED IDEOGRAPH-6A17
- Cell 10: U+6AA3 `檣` CJK UNIFIED IDEOGRAPH-6AA3
- Cell 11: U+7F45 `罅` CJK UNIFIED IDEOGRAPH-7F45
- Cell 12: U+7FEE `翮` CJK UNIFIED IDEOGRAPH-7FEE
- Cell 13: U+84D1 `蓑` CJK UNIFIED IDEOGRAPH-84D1
- Cell 14: U+89DA `觚` CJK UNIFIED IDEOGRAPH-89DA
- Cell 15: U+8DE4 `跤` CJK UNIFIED IDEOGRAPH-8DE4
- Cell 16: U+5B2D `嬭` CJK UNIFIED IDEOGRAPH-5B2D

Text (verbatim):
虺跖酶醴
閬倈哏徼
樗檣罅翮
蓑觚跤嬭

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
