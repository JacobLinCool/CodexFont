# Image-generated Han-delta sheet dict-han-0054

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0054.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0054.png` (`f45df1f1b888c26fa9961ee9c5c83945fe68eb75be17bb4e4f6cf493da511762`)
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
嗝圇奼嫠 / 嬙嵯忡怫 / 惸扞搴斕 / 昃栲桷欷.

Exact occupied cells:
- Cell 01: U+55DD `嗝` CJK UNIFIED IDEOGRAPH-55DD
- Cell 02: U+5707 `圇` CJK UNIFIED IDEOGRAPH-5707
- Cell 03: U+597C `奼` CJK UNIFIED IDEOGRAPH-597C
- Cell 04: U+5AE0 `嫠` CJK UNIFIED IDEOGRAPH-5AE0
- Cell 05: U+5B19 `嬙` CJK UNIFIED IDEOGRAPH-5B19
- Cell 06: U+5D6F `嵯` CJK UNIFIED IDEOGRAPH-5D6F
- Cell 07: U+5FE1 `忡` CJK UNIFIED IDEOGRAPH-5FE1
- Cell 08: U+602B `怫` CJK UNIFIED IDEOGRAPH-602B
- Cell 09: U+60F8 `惸` CJK UNIFIED IDEOGRAPH-60F8
- Cell 10: U+625E `扞` CJK UNIFIED IDEOGRAPH-625E
- Cell 11: U+6434 `搴` CJK UNIFIED IDEOGRAPH-6434
- Cell 12: U+6595 `斕` CJK UNIFIED IDEOGRAPH-6595
- Cell 13: U+6603 `昃` CJK UNIFIED IDEOGRAPH-6603
- Cell 14: U+6832 `栲` CJK UNIFIED IDEOGRAPH-6832
- Cell 15: U+6877 `桷` CJK UNIFIED IDEOGRAPH-6877
- Cell 16: U+6B37 `欷` CJK UNIFIED IDEOGRAPH-6B37

Text (verbatim):
嗝圇奼嫠
嬙嵯忡怫
惸扞搴斕
昃栲桷欷

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
