# Image-generated Han-delta sheet dict-han-0029

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0029.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0029.png` (`27b0076b527019d51c0c250760ac8bac0af48142d91d0b28257a133711d3192f`)
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
嬖廕怛扃 / 挹揎搠暝 / 槅炷猊猢 / 猻甑緲縵.

Exact occupied cells:
- Cell 01: U+5B16 `嬖` CJK UNIFIED IDEOGRAPH-5B16
- Cell 02: U+5ED5 `廕` CJK UNIFIED IDEOGRAPH-5ED5
- Cell 03: U+601B `怛` CJK UNIFIED IDEOGRAPH-601B
- Cell 04: U+6243 `扃` CJK UNIFIED IDEOGRAPH-6243
- Cell 05: U+6339 `挹` CJK UNIFIED IDEOGRAPH-6339
- Cell 06: U+63CE `揎` CJK UNIFIED IDEOGRAPH-63CE
- Cell 07: U+6420 `搠` CJK UNIFIED IDEOGRAPH-6420
- Cell 08: U+669D `暝` CJK UNIFIED IDEOGRAPH-669D
- Cell 09: U+69C5 `槅` CJK UNIFIED IDEOGRAPH-69C5
- Cell 10: U+70B7 `炷` CJK UNIFIED IDEOGRAPH-70B7
- Cell 11: U+730A `猊` CJK UNIFIED IDEOGRAPH-730A
- Cell 12: U+7322 `猢` CJK UNIFIED IDEOGRAPH-7322
- Cell 13: U+733B `猻` CJK UNIFIED IDEOGRAPH-733B
- Cell 14: U+7511 `甑` CJK UNIFIED IDEOGRAPH-7511
- Cell 15: U+7DF2 `緲` CJK UNIFIED IDEOGRAPH-7DF2
- Cell 16: U+7E35 `縵` CJK UNIFIED IDEOGRAPH-7E35

Text (verbatim):
嬖廕怛扃
挹揎搠暝
槅炷猊猢
猻甑緲縵

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
