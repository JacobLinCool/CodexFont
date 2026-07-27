# Image-generated Han-delta sheet dict-han-0058

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0058.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0058.png` (`8e5b2184f5dafc3e6cf5f8d5fcc2ff3a5ecb9b3b5929c14ebf27bbd25f8baf22`)
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
堠墉壎尻 / 峴悁拶掎 / 揄斁枵柝 / 櫱殭涔濰.

Exact occupied cells:
- Cell 01: U+5820 `堠` CJK UNIFIED IDEOGRAPH-5820
- Cell 02: U+5889 `墉` CJK UNIFIED IDEOGRAPH-5889
- Cell 03: U+58CE `壎` CJK UNIFIED IDEOGRAPH-58CE
- Cell 04: U+5C3B `尻` CJK UNIFIED IDEOGRAPH-5C3B
- Cell 05: U+5CF4 `峴` CJK UNIFIED IDEOGRAPH-5CF4
- Cell 06: U+6081 `悁` CJK UNIFIED IDEOGRAPH-6081
- Cell 07: U+62F6 `拶` CJK UNIFIED IDEOGRAPH-62F6
- Cell 08: U+638E `掎` CJK UNIFIED IDEOGRAPH-638E
- Cell 09: U+63C4 `揄` CJK UNIFIED IDEOGRAPH-63C4
- Cell 10: U+6581 `斁` CJK UNIFIED IDEOGRAPH-6581
- Cell 11: U+67B5 `枵` CJK UNIFIED IDEOGRAPH-67B5
- Cell 12: U+67DD `柝` CJK UNIFIED IDEOGRAPH-67DD
- Cell 13: U+6AF1 `櫱` CJK UNIFIED IDEOGRAPH-6AF1
- Cell 14: U+6BAD `殭` CJK UNIFIED IDEOGRAPH-6BAD
- Cell 15: U+6D94 `涔` CJK UNIFIED IDEOGRAPH-6D94
- Cell 16: U+6FF0 `濰` CJK UNIFIED IDEOGRAPH-6FF0

Text (verbatim):
堠墉壎尻
峴悁拶掎
揄斁枵柝
櫱殭涔濰

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
