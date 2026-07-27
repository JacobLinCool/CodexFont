# Image-generated Han-delta sheet dict-han-0025

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0025.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0025.png` (`b3ec0ffa03241af41525fc7d1241f187f8dde15221efe31e897e075fb1091400`)
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
眥磣縝縞 / 耦苯菟蔻 / 賚趄鍘鎬 / 闥龕俛傒.

Exact occupied cells:
- Cell 01: U+7725 `眥` CJK UNIFIED IDEOGRAPH-7725
- Cell 02: U+78E3 `磣` CJK UNIFIED IDEOGRAPH-78E3
- Cell 03: U+7E1D `縝` CJK UNIFIED IDEOGRAPH-7E1D
- Cell 04: U+7E1E `縞` CJK UNIFIED IDEOGRAPH-7E1E
- Cell 05: U+8026 `耦` CJK UNIFIED IDEOGRAPH-8026
- Cell 06: U+82EF `苯` CJK UNIFIED IDEOGRAPH-82EF
- Cell 07: U+83DF `菟` CJK UNIFIED IDEOGRAPH-83DF
- Cell 08: U+853B `蔻` CJK UNIFIED IDEOGRAPH-853B
- Cell 09: U+8CDA `賚` CJK UNIFIED IDEOGRAPH-8CDA
- Cell 10: U+8D84 `趄` CJK UNIFIED IDEOGRAPH-8D84
- Cell 11: U+9358 `鍘` CJK UNIFIED IDEOGRAPH-9358
- Cell 12: U+93AC `鎬` CJK UNIFIED IDEOGRAPH-93AC
- Cell 13: U+95E5 `闥` CJK UNIFIED IDEOGRAPH-95E5
- Cell 14: U+9F95 `龕` CJK UNIFIED IDEOGRAPH-9F95
- Cell 15: U+4FDB `俛` CJK UNIFIED IDEOGRAPH-4FDB
- Cell 16: U+5092 `傒` CJK UNIFIED IDEOGRAPH-5092

Text (verbatim):
眥磣縝縞
耦苯菟蔻
賚趄鍘鎬
闥龕俛傒

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
