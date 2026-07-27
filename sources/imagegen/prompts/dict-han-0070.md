# Image-generated Han-delta sheet dict-han-0070

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0070.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0070.png` (`4e61c1f585d089b29b556cf7d3dbcc9a7cfc03732b7cf6960154690a94417e59`)
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
偪儋儗儹 / 嗹噍嚙埴 / 堞宄岈岧 / 嵒忭忸掿.

Exact occupied cells:
- Cell 01: U+506A `偪` CJK UNIFIED IDEOGRAPH-506A
- Cell 02: U+510B `儋` CJK UNIFIED IDEOGRAPH-510B
- Cell 03: U+5117 `儗` CJK UNIFIED IDEOGRAPH-5117
- Cell 04: U+5139 `儹` CJK UNIFIED IDEOGRAPH-5139
- Cell 05: U+55F9 `嗹` CJK UNIFIED IDEOGRAPH-55F9
- Cell 06: U+564D `噍` CJK UNIFIED IDEOGRAPH-564D
- Cell 07: U+5699 `嚙` CJK UNIFIED IDEOGRAPH-5699
- Cell 08: U+57F4 `埴` CJK UNIFIED IDEOGRAPH-57F4
- Cell 09: U+581E `堞` CJK UNIFIED IDEOGRAPH-581E
- Cell 10: U+5B84 `宄` CJK UNIFIED IDEOGRAPH-5B84
- Cell 11: U+5C88 `岈` CJK UNIFIED IDEOGRAPH-5C88
- Cell 12: U+5CA7 `岧` CJK UNIFIED IDEOGRAPH-5CA7
- Cell 13: U+5D52 `嵒` CJK UNIFIED IDEOGRAPH-5D52
- Cell 14: U+5FED `忭` CJK UNIFIED IDEOGRAPH-5FED
- Cell 15: U+5FF8 `忸` CJK UNIFIED IDEOGRAPH-5FF8
- Cell 16: U+63BF `掿` CJK UNIFIED IDEOGRAPH-63BF

Text (verbatim):
偪儋儗儹
嗹噍嚙埴
堞宄岈岧
嵒忭忸掿

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
