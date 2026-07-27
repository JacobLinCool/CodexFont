# Image-generated Han-delta sheet dict-han-0052

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0052.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0052.png` (`680b43382261ddc90820a21650343f611ae3e62d58d86d025a797e40f3dc555a`)
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
痼睍瞼秸 / 綆耨臠臢 / 舳芊菫葆 / 訇蹐躧逡.

Exact occupied cells:
- Cell 01: U+75FC `痼` CJK UNIFIED IDEOGRAPH-75FC
- Cell 02: U+774D `睍` CJK UNIFIED IDEOGRAPH-774D
- Cell 03: U+77BC `瞼` CJK UNIFIED IDEOGRAPH-77BC
- Cell 04: U+79F8 `秸` CJK UNIFIED IDEOGRAPH-79F8
- Cell 05: U+7D86 `綆` CJK UNIFIED IDEOGRAPH-7D86
- Cell 06: U+8028 `耨` CJK UNIFIED IDEOGRAPH-8028
- Cell 07: U+81E0 `臠` CJK UNIFIED IDEOGRAPH-81E0
- Cell 08: U+81E2 `臢` CJK UNIFIED IDEOGRAPH-81E2
- Cell 09: U+8233 `舳` CJK UNIFIED IDEOGRAPH-8233
- Cell 10: U+828A `芊` CJK UNIFIED IDEOGRAPH-828A
- Cell 11: U+83EB `菫` CJK UNIFIED IDEOGRAPH-83EB
- Cell 12: U+8446 `葆` CJK UNIFIED IDEOGRAPH-8446
- Cell 13: U+8A07 `訇` CJK UNIFIED IDEOGRAPH-8A07
- Cell 14: U+8E50 `蹐` CJK UNIFIED IDEOGRAPH-8E50
- Cell 15: U+8EA7 `躧` CJK UNIFIED IDEOGRAPH-8EA7
- Cell 16: U+9021 `逡` CJK UNIFIED IDEOGRAPH-9021

Text (verbatim):
痼睍瞼秸
綆耨臠臢
舳芊菫葆
訇蹐躧逡

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
