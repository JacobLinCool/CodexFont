# Image-generated Han-delta sheet dict-han-0004

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0004.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0004.png` (`258631638c59ed629e4dfd136b9cd4e7acbd685d96e418cddb3989ee4a3f33b4`)
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
翦珪糶劄 / 鈿饋拏檯 / 邯偁廩攛 / 皁墩彊憨.

Exact occupied cells:
- Cell 01: U+7FE6 `翦` CJK UNIFIED IDEOGRAPH-7FE6
- Cell 02: U+73EA `珪` CJK UNIFIED IDEOGRAPH-73EA
- Cell 03: U+7CF6 `糶` CJK UNIFIED IDEOGRAPH-7CF6
- Cell 04: U+5284 `劄` CJK UNIFIED IDEOGRAPH-5284
- Cell 05: U+923F `鈿` CJK UNIFIED IDEOGRAPH-923F
- Cell 06: U+994B `饋` CJK UNIFIED IDEOGRAPH-994B
- Cell 07: U+62CF `拏` CJK UNIFIED IDEOGRAPH-62CF
- Cell 08: U+6AAF `檯` CJK UNIFIED IDEOGRAPH-6AAF
- Cell 09: U+90AF `邯` CJK UNIFIED IDEOGRAPH-90AF
- Cell 10: U+5041 `偁` CJK UNIFIED IDEOGRAPH-5041
- Cell 11: U+5EE9 `廩` CJK UNIFIED IDEOGRAPH-5EE9
- Cell 12: U+651B `攛` CJK UNIFIED IDEOGRAPH-651B
- Cell 13: U+7681 `皁` CJK UNIFIED IDEOGRAPH-7681
- Cell 14: U+58A9 `墩` CJK UNIFIED IDEOGRAPH-58A9
- Cell 15: U+5F4A `彊` CJK UNIFIED IDEOGRAPH-5F4A
- Cell 16: U+61A8 `憨` CJK UNIFIED IDEOGRAPH-61A8

Text (verbatim):
翦珪糶劄
鈿饋拏檯
邯偁廩攛
皁墩彊憨

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
