# Image-generated Han-delta sheet dict-han-0065

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0065.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0065.png` (`355fbce60a26957fd1a056eb90d6e7d90f11d717facfaf326f4067b30f392a37`)
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
轤遛郤鄠 / 釅閶陬霰 / 鞚頲颻饃 / 驩髴鬯鯖.

Exact occupied cells:
- Cell 01: U+8F64 `轤` CJK UNIFIED IDEOGRAPH-8F64
- Cell 02: U+905B `遛` CJK UNIFIED IDEOGRAPH-905B
- Cell 03: U+90E4 `郤` CJK UNIFIED IDEOGRAPH-90E4
- Cell 04: U+9120 `鄠` CJK UNIFIED IDEOGRAPH-9120
- Cell 05: U+91C5 `釅` CJK UNIFIED IDEOGRAPH-91C5
- Cell 06: U+95B6 `閶` CJK UNIFIED IDEOGRAPH-95B6
- Cell 07: U+966C `陬` CJK UNIFIED IDEOGRAPH-966C
- Cell 08: U+9730 `霰` CJK UNIFIED IDEOGRAPH-9730
- Cell 09: U+979A `鞚` CJK UNIFIED IDEOGRAPH-979A
- Cell 10: U+9832 `頲` CJK UNIFIED IDEOGRAPH-9832
- Cell 11: U+98BB `颻` CJK UNIFIED IDEOGRAPH-98BB
- Cell 12: U+9943 `饃` CJK UNIFIED IDEOGRAPH-9943
- Cell 13: U+9A69 `驩` CJK UNIFIED IDEOGRAPH-9A69
- Cell 14: U+9AF4 `髴` CJK UNIFIED IDEOGRAPH-9AF4
- Cell 15: U+9B2F `鬯` CJK UNIFIED IDEOGRAPH-9B2F
- Cell 16: U+9BD6 `鯖` CJK UNIFIED IDEOGRAPH-9BD6

Text (verbatim):
轤遛郤鄠
釅閶陬霰
鞚頲颻饃
驩髴鬯鯖

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
