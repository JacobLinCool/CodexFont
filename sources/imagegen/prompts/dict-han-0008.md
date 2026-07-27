# Image-generated Han-delta sheet dict-han-0008

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0008.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0008.png` (`3ab743e0ea97c329aefe61c43aad81119f9d9d640d2917e9e5ce047df84bcf62`)
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
顥勺幃穰 / 昊秘飆齧 / 曇歆牋嫋 / 愆杓泯瀧.

Exact occupied cells:
- Cell 01: U+9865 `顥` CJK UNIFIED IDEOGRAPH-9865
- Cell 02: U+52FA `勺` CJK UNIFIED IDEOGRAPH-52FA
- Cell 03: U+5E43 `幃` CJK UNIFIED IDEOGRAPH-5E43
- Cell 04: U+7A70 `穰` CJK UNIFIED IDEOGRAPH-7A70
- Cell 05: U+660A `昊` CJK UNIFIED IDEOGRAPH-660A
- Cell 06: U+79D8 `秘` CJK UNIFIED IDEOGRAPH-79D8
- Cell 07: U+98C6 `飆` CJK UNIFIED IDEOGRAPH-98C6
- Cell 08: U+9F67 `齧` CJK UNIFIED IDEOGRAPH-9F67
- Cell 09: U+66C7 `曇` CJK UNIFIED IDEOGRAPH-66C7
- Cell 10: U+6B46 `歆` CJK UNIFIED IDEOGRAPH-6B46
- Cell 11: U+724B `牋` CJK UNIFIED IDEOGRAPH-724B
- Cell 12: U+5ACB `嫋` CJK UNIFIED IDEOGRAPH-5ACB
- Cell 13: U+6106 `愆` CJK UNIFIED IDEOGRAPH-6106
- Cell 14: U+6753 `杓` CJK UNIFIED IDEOGRAPH-6753
- Cell 15: U+6CEF `泯` CJK UNIFIED IDEOGRAPH-6CEF
- Cell 16: U+7027 `瀧` CJK UNIFIED IDEOGRAPH-7027

Text (verbatim):
顥勺幃穰
昊秘飆齧
曇歆牋嫋
愆杓泯瀧

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
