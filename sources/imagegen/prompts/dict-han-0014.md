# Image-generated Han-delta sheet dict-han-0014

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0014.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0014.png` (`5ecf62566bb76d082c0c8c37a6dcad1a7854bac4f79581f25ab65345366e9ed3`)
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
喒噶撾蹴 / 鶚鷲齎仝 / 徭擣暄浹 / 涿甯碴苴.

Exact occupied cells:
- Cell 01: U+5592 `喒` CJK UNIFIED IDEOGRAPH-5592
- Cell 02: U+5676 `噶` CJK UNIFIED IDEOGRAPH-5676
- Cell 03: U+64BE `撾` CJK UNIFIED IDEOGRAPH-64BE
- Cell 04: U+8E74 `蹴` CJK UNIFIED IDEOGRAPH-8E74
- Cell 05: U+9D9A `鶚` CJK UNIFIED IDEOGRAPH-9D9A
- Cell 06: U+9DF2 `鷲` CJK UNIFIED IDEOGRAPH-9DF2
- Cell 07: U+9F4E `齎` CJK UNIFIED IDEOGRAPH-9F4E
- Cell 08: U+4EDD `仝` CJK UNIFIED IDEOGRAPH-4EDD
- Cell 09: U+5FAD `徭` CJK UNIFIED IDEOGRAPH-5FAD
- Cell 10: U+64E3 `擣` CJK UNIFIED IDEOGRAPH-64E3
- Cell 11: U+6684 `暄` CJK UNIFIED IDEOGRAPH-6684
- Cell 12: U+6D79 `浹` CJK UNIFIED IDEOGRAPH-6D79
- Cell 13: U+6DBF `涿` CJK UNIFIED IDEOGRAPH-6DBF
- Cell 14: U+752F `甯` CJK UNIFIED IDEOGRAPH-752F
- Cell 15: U+78B4 `碴` CJK UNIFIED IDEOGRAPH-78B4
- Cell 16: U+82F4 `苴` CJK UNIFIED IDEOGRAPH-82F4

Text (verbatim):
喒噶撾蹴
鶚鷲齎仝
徭擣暄浹
涿甯碴苴

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
