# Image-generated Han-delta sheet dict-han-0042

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0042.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0042.png` (`23842f7d208a8647565fc279ba30eca89a48375e9115ae2844a6471b2e38374e`)
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
蹠逶酹銃 / 閼阨颩飫 / 騮鮒鷟乂 / 傚嘓壚媧.

Exact occupied cells:
- Cell 01: U+8E60 `蹠` CJK UNIFIED IDEOGRAPH-8E60
- Cell 02: U+9036 `逶` CJK UNIFIED IDEOGRAPH-9036
- Cell 03: U+9179 `酹` CJK UNIFIED IDEOGRAPH-9179
- Cell 04: U+9283 `銃` CJK UNIFIED IDEOGRAPH-9283
- Cell 05: U+95BC `閼` CJK UNIFIED IDEOGRAPH-95BC
- Cell 06: U+9628 `阨` CJK UNIFIED IDEOGRAPH-9628
- Cell 07: U+98A9 `颩` CJK UNIFIED IDEOGRAPH-98A9
- Cell 08: U+98EB `飫` CJK UNIFIED IDEOGRAPH-98EB
- Cell 09: U+9A2E `騮` CJK UNIFIED IDEOGRAPH-9A2E
- Cell 10: U+9B92 `鮒` CJK UNIFIED IDEOGRAPH-9B92
- Cell 11: U+9DDF `鷟` CJK UNIFIED IDEOGRAPH-9DDF
- Cell 12: U+4E42 `乂` CJK UNIFIED IDEOGRAPH-4E42
- Cell 13: U+509A `傚` CJK UNIFIED IDEOGRAPH-509A
- Cell 14: U+5613 `嘓` CJK UNIFIED IDEOGRAPH-5613
- Cell 15: U+58DA `壚` CJK UNIFIED IDEOGRAPH-58DA
- Cell 16: U+5AA7 `媧` CJK UNIFIED IDEOGRAPH-5AA7

Text (verbatim):
蹠逶酹銃
閼阨颩飫
騮鮒鷟乂
傚嘓壚媧

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
