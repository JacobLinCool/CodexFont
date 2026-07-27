# Image-generated Han-delta sheet dict-han-0039

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0039.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0039.png` (`b0bfae19c19a53e902d03151666793b462401e5527a7e1c22b67f161092bd891`)
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
剡圉坂怙 / 掰擀槧橛 / 洄淩煨磔 / 筌糴絰纛.

Exact occupied cells:
- Cell 01: U+5261 `剡` CJK UNIFIED IDEOGRAPH-5261
- Cell 02: U+5709 `圉` CJK UNIFIED IDEOGRAPH-5709
- Cell 03: U+5742 `坂` CJK UNIFIED IDEOGRAPH-5742
- Cell 04: U+6019 `怙` CJK UNIFIED IDEOGRAPH-6019
- Cell 05: U+63B0 `掰` CJK UNIFIED IDEOGRAPH-63B0
- Cell 06: U+64C0 `擀` CJK UNIFIED IDEOGRAPH-64C0
- Cell 07: U+69E7 `槧` CJK UNIFIED IDEOGRAPH-69E7
- Cell 08: U+6A5B `橛` CJK UNIFIED IDEOGRAPH-6A5B
- Cell 09: U+6D04 `洄` CJK UNIFIED IDEOGRAPH-6D04
- Cell 10: U+6DE9 `淩` CJK UNIFIED IDEOGRAPH-6DE9
- Cell 11: U+7168 `煨` CJK UNIFIED IDEOGRAPH-7168
- Cell 12: U+78D4 `磔` CJK UNIFIED IDEOGRAPH-78D4
- Cell 13: U+7B4C `筌` CJK UNIFIED IDEOGRAPH-7B4C
- Cell 14: U+7CF4 `糴` CJK UNIFIED IDEOGRAPH-7CF4
- Cell 15: U+7D70 `絰` CJK UNIFIED IDEOGRAPH-7D70
- Cell 16: U+7E9B `纛` CJK UNIFIED IDEOGRAPH-7E9B

Text (verbatim):
剡圉坂怙
掰擀槧橛
洄淩煨磔
筌糴絰纛

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
