# Image-generated Han-delta sheet dict-han-0056

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0056.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0056.png` (`1dbbf98a5c96852a04ffc3184b360f3295677b351324f1f30aaa5ae2ad238437`)
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
粼胝荳菑 / 藎藷袷裀 / 褙豳蹕迍 / 逩郯醚醛.

Exact occupied cells:
- Cell 01: U+7CBC `粼` CJK UNIFIED IDEOGRAPH-7CBC
- Cell 02: U+80DD `胝` CJK UNIFIED IDEOGRAPH-80DD
- Cell 03: U+8373 `荳` CJK UNIFIED IDEOGRAPH-8373
- Cell 04: U+83D1 `菑` CJK UNIFIED IDEOGRAPH-83D1
- Cell 05: U+85CE `藎` CJK UNIFIED IDEOGRAPH-85CE
- Cell 06: U+85F7 `藷` CJK UNIFIED IDEOGRAPH-85F7
- Cell 07: U+88B7 `袷` CJK UNIFIED IDEOGRAPH-88B7
- Cell 08: U+88C0 `裀` CJK UNIFIED IDEOGRAPH-88C0
- Cell 09: U+8919 `褙` CJK UNIFIED IDEOGRAPH-8919
- Cell 10: U+8C73 `豳` CJK UNIFIED IDEOGRAPH-8C73
- Cell 11: U+8E55 `蹕` CJK UNIFIED IDEOGRAPH-8E55
- Cell 12: U+8FCD `迍` CJK UNIFIED IDEOGRAPH-8FCD
- Cell 13: U+9029 `逩` CJK UNIFIED IDEOGRAPH-9029
- Cell 14: U+90EF `郯` CJK UNIFIED IDEOGRAPH-90EF
- Cell 15: U+919A `醚` CJK UNIFIED IDEOGRAPH-919A
- Cell 16: U+919B `醛` CJK UNIFIED IDEOGRAPH-919B

Text (verbatim):
粼胝荳菑
藎藷袷裀
褙豳蹕迍
逩郯醚醛

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
