# Image-generated Han-delta sheet dict-han-0028

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0028.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0028.png` (`66ea6287b65c0afa06db79035713accda9d0dac82746066836dc9d03e4c05cf2`)
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
杌櫪溷璟 / 甓碓糰罡 / 翶胯薏虀 / 蜍儕冪咂.

Exact occupied cells:
- Cell 01: U+674C `杌` CJK UNIFIED IDEOGRAPH-674C
- Cell 02: U+6AEA `櫪` CJK UNIFIED IDEOGRAPH-6AEA
- Cell 03: U+6EB7 `溷` CJK UNIFIED IDEOGRAPH-6EB7
- Cell 04: U+749F `璟` CJK UNIFIED IDEOGRAPH-749F
- Cell 05: U+7513 `甓` CJK UNIFIED IDEOGRAPH-7513
- Cell 06: U+7893 `碓` CJK UNIFIED IDEOGRAPH-7893
- Cell 07: U+7CF0 `糰` CJK UNIFIED IDEOGRAPH-7CF0
- Cell 08: U+7F61 `罡` CJK UNIFIED IDEOGRAPH-7F61
- Cell 09: U+7FF6 `翶` CJK UNIFIED IDEOGRAPH-7FF6
- Cell 10: U+80EF `胯` CJK UNIFIED IDEOGRAPH-80EF
- Cell 11: U+858F `薏` CJK UNIFIED IDEOGRAPH-858F
- Cell 12: U+8640 `虀` CJK UNIFIED IDEOGRAPH-8640
- Cell 13: U+870D `蜍` CJK UNIFIED IDEOGRAPH-870D
- Cell 14: U+5115 `儕` CJK UNIFIED IDEOGRAPH-5115
- Cell 15: U+51AA `冪` CJK UNIFIED IDEOGRAPH-51AA
- Cell 16: U+5482 `咂` CJK UNIFIED IDEOGRAPH-5482

Text (verbatim):
杌櫪溷璟
甓碓糰罡
翶胯薏虀
蜍儕冪咂

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
