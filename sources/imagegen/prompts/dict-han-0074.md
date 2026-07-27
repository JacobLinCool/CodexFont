# Image-generated Han-delta sheet dict-han-0074

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0074.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0074.png` (`599dfc4411b955ec0d69808d411c5f32ec45593d79088a1691c15f51b330a141`)
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
霈餖餳饝 / 騅鬒鶼黄 / 仵佤佶倅 / 僝呦哧唚.

Exact occupied cells:
- Cell 01: U+9708 `霈` CJK UNIFIED IDEOGRAPH-9708
- Cell 02: U+9916 `餖` CJK UNIFIED IDEOGRAPH-9916
- Cell 03: U+9933 `餳` CJK UNIFIED IDEOGRAPH-9933
- Cell 04: U+995D `饝` CJK UNIFIED IDEOGRAPH-995D
- Cell 05: U+9A05 `騅` CJK UNIFIED IDEOGRAPH-9A05
- Cell 06: U+9B12 `鬒` CJK UNIFIED IDEOGRAPH-9B12
- Cell 07: U+9DBC `鶼` CJK UNIFIED IDEOGRAPH-9DBC
- Cell 08: U+9EC4 `黄` CJK UNIFIED IDEOGRAPH-9EC4
- Cell 09: U+4EF5 `仵` CJK UNIFIED IDEOGRAPH-4EF5
- Cell 10: U+4F64 `佤` CJK UNIFIED IDEOGRAPH-4F64
- Cell 11: U+4F76 `佶` CJK UNIFIED IDEOGRAPH-4F76
- Cell 12: U+5005 `倅` CJK UNIFIED IDEOGRAPH-5005
- Cell 13: U+50DD `僝` CJK UNIFIED IDEOGRAPH-50DD
- Cell 14: U+5466 `呦` CJK UNIFIED IDEOGRAPH-5466
- Cell 15: U+54E7 `哧` CJK UNIFIED IDEOGRAPH-54E7
- Cell 16: U+551A `唚` CJK UNIFIED IDEOGRAPH-551A

Text (verbatim):
霈餖餳饝
騅鬒鶼黄
仵佤佶倅
僝呦哧唚

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
