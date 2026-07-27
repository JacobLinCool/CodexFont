# Image-generated Han-delta sheet dict-han-0033

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0033.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0033.png` (`0c1beeae35deb12527a32c7924c414be69abbac28b250822e04463a29b107b59`)
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
楂泵湜烷 / 玕璇瓤疱 / 禊穠篳紵 / 絛苡莧蓐.

Exact occupied cells:
- Cell 01: U+6942 `楂` CJK UNIFIED IDEOGRAPH-6942
- Cell 02: U+6CF5 `泵` CJK UNIFIED IDEOGRAPH-6CF5
- Cell 03: U+6E5C `湜` CJK UNIFIED IDEOGRAPH-6E5C
- Cell 04: U+70F7 `烷` CJK UNIFIED IDEOGRAPH-70F7
- Cell 05: U+7395 `玕` CJK UNIFIED IDEOGRAPH-7395
- Cell 06: U+7487 `璇` CJK UNIFIED IDEOGRAPH-7487
- Cell 07: U+74E4 `瓤` CJK UNIFIED IDEOGRAPH-74E4
- Cell 08: U+75B1 `疱` CJK UNIFIED IDEOGRAPH-75B1
- Cell 09: U+798A `禊` CJK UNIFIED IDEOGRAPH-798A
- Cell 10: U+7A60 `穠` CJK UNIFIED IDEOGRAPH-7A60
- Cell 11: U+7BF3 `篳` CJK UNIFIED IDEOGRAPH-7BF3
- Cell 12: U+7D35 `紵` CJK UNIFIED IDEOGRAPH-7D35
- Cell 13: U+7D5B `絛` CJK UNIFIED IDEOGRAPH-7D5B
- Cell 14: U+82E1 `苡` CJK UNIFIED IDEOGRAPH-82E1
- Cell 15: U+83A7 `莧` CJK UNIFIED IDEOGRAPH-83A7
- Cell 16: U+84D0 `蓐` CJK UNIFIED IDEOGRAPH-84D0

Text (verbatim):
楂泵湜烷
玕璇瓤疱
禊穠篳紵
絛苡莧蓐

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
