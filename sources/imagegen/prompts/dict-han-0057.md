# Image-generated Han-delta sheet dict-han-0057

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0057.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0057.png` (`df5b2be782ce3c5a4e107e06f33213598457b8d34b69dbcff91ea89c61d6bffb`)
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
錙鑞餗餬 / 餼饉髖髣 / 魆鷙卬哆 / 囓垤埒堙.

Exact occupied cells:
- Cell 01: U+9319 `錙` CJK UNIFIED IDEOGRAPH-9319
- Cell 02: U+945E `鑞` CJK UNIFIED IDEOGRAPH-945E
- Cell 03: U+9917 `餗` CJK UNIFIED IDEOGRAPH-9917
- Cell 04: U+992C `餬` CJK UNIFIED IDEOGRAPH-992C
- Cell 05: U+993C `餼` CJK UNIFIED IDEOGRAPH-993C
- Cell 06: U+9949 `饉` CJK UNIFIED IDEOGRAPH-9949
- Cell 07: U+9AD6 `髖` CJK UNIFIED IDEOGRAPH-9AD6
- Cell 08: U+9AE3 `髣` CJK UNIFIED IDEOGRAPH-9AE3
- Cell 09: U+9B46 `魆` CJK UNIFIED IDEOGRAPH-9B46
- Cell 10: U+9DD9 `鷙` CJK UNIFIED IDEOGRAPH-9DD9
- Cell 11: U+536C `卬` CJK UNIFIED IDEOGRAPH-536C
- Cell 12: U+54C6 `哆` CJK UNIFIED IDEOGRAPH-54C6
- Cell 13: U+56D3 `囓` CJK UNIFIED IDEOGRAPH-56D3
- Cell 14: U+57A4 `垤` CJK UNIFIED IDEOGRAPH-57A4
- Cell 15: U+57D2 `埒` CJK UNIFIED IDEOGRAPH-57D2
- Cell 16: U+5819 `堙` CJK UNIFIED IDEOGRAPH-5819

Text (verbatim):
錙鑞餗餬
餼饉髖髣
魆鷙卬哆
囓垤埒堙

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
