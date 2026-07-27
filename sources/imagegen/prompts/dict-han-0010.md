# Image-generated Han-delta sheet dict-han-0010

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0010.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0010.png` (`a70da9ccabe5b906ffc42e765c4be41833dae3e88e1ee7cf1758cc4fee876049`)
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
剗咧喙楮 / 沂碣闇驍 / 嵬洵滷烯 / 祜箍觔諳.

Exact occupied cells:
- Cell 01: U+5257 `剗` CJK UNIFIED IDEOGRAPH-5257
- Cell 02: U+54A7 `咧` CJK UNIFIED IDEOGRAPH-54A7
- Cell 03: U+5599 `喙` CJK UNIFIED IDEOGRAPH-5599
- Cell 04: U+696E `楮` CJK UNIFIED IDEOGRAPH-696E
- Cell 05: U+6C82 `沂` CJK UNIFIED IDEOGRAPH-6C82
- Cell 06: U+78A3 `碣` CJK UNIFIED IDEOGRAPH-78A3
- Cell 07: U+95C7 `闇` CJK UNIFIED IDEOGRAPH-95C7
- Cell 08: U+9A4D `驍` CJK UNIFIED IDEOGRAPH-9A4D
- Cell 09: U+5D6C `嵬` CJK UNIFIED IDEOGRAPH-5D6C
- Cell 10: U+6D35 `洵` CJK UNIFIED IDEOGRAPH-6D35
- Cell 11: U+6EF7 `滷` CJK UNIFIED IDEOGRAPH-6EF7
- Cell 12: U+70EF `烯` CJK UNIFIED IDEOGRAPH-70EF
- Cell 13: U+795C `祜` CJK UNIFIED IDEOGRAPH-795C
- Cell 14: U+7B8D `箍` CJK UNIFIED IDEOGRAPH-7B8D
- Cell 15: U+89D4 `觔` CJK UNIFIED IDEOGRAPH-89D4
- Cell 16: U+8AF3 `諳` CJK UNIFIED IDEOGRAPH-8AF3

Text (verbatim):
剗咧喙楮
沂碣闇驍
嵬洵滷烯
祜箍觔諳

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
