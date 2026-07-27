# Image-generated Han-delta sheet dict-han-0048

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0048.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0048.png` (`e6caca7f18ba27d6f616ae1aa7393c8d6afe2069390631b83ead25230b90cf31`)
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
倜儸冏咍 / 囫壼宓捍 / 揜搊昱晾 / 楸渰瀘燠.

Exact occupied cells:
- Cell 01: U+501C `倜` CJK UNIFIED IDEOGRAPH-501C
- Cell 02: U+5138 `儸` CJK UNIFIED IDEOGRAPH-5138
- Cell 03: U+518F `冏` CJK UNIFIED IDEOGRAPH-518F
- Cell 04: U+548D `咍` CJK UNIFIED IDEOGRAPH-548D
- Cell 05: U+56EB `囫` CJK UNIFIED IDEOGRAPH-56EB
- Cell 06: U+58FC `壼` CJK UNIFIED IDEOGRAPH-58FC
- Cell 07: U+5B93 `宓` CJK UNIFIED IDEOGRAPH-5B93
- Cell 08: U+634D `捍` CJK UNIFIED IDEOGRAPH-634D
- Cell 09: U+63DC `揜` CJK UNIFIED IDEOGRAPH-63DC
- Cell 10: U+640A `搊` CJK UNIFIED IDEOGRAPH-640A
- Cell 11: U+6631 `昱` CJK UNIFIED IDEOGRAPH-6631
- Cell 12: U+667E `晾` CJK UNIFIED IDEOGRAPH-667E
- Cell 13: U+6978 `楸` CJK UNIFIED IDEOGRAPH-6978
- Cell 14: U+6E30 `渰` CJK UNIFIED IDEOGRAPH-6E30
- Cell 15: U+7018 `瀘` CJK UNIFIED IDEOGRAPH-7018
- Cell 16: U+71E0 `燠` CJK UNIFIED IDEOGRAPH-71E0

Text (verbatim):
倜儸冏咍
囫壼宓捍
揜搊昱晾
楸渰瀘燠

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
