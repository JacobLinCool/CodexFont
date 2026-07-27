# Image-generated Han-delta sheet dict-han-0035

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0035.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0035.png` (`4ccb5a69561a129faa5398f8ae7167921d13474cf0b6ed779ff33aac232fe185`)
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
厘娉嶢彘 / 恂恓戧搐 / 摳曩燾甍 / 窅窨萁袤.

Exact occupied cells:
- Cell 01: U+5398 `厘` CJK UNIFIED IDEOGRAPH-5398
- Cell 02: U+5A09 `娉` CJK UNIFIED IDEOGRAPH-5A09
- Cell 03: U+5DA2 `嶢` CJK UNIFIED IDEOGRAPH-5DA2
- Cell 04: U+5F58 `彘` CJK UNIFIED IDEOGRAPH-5F58
- Cell 05: U+6042 `恂` CJK UNIFIED IDEOGRAPH-6042
- Cell 06: U+6053 `恓` CJK UNIFIED IDEOGRAPH-6053
- Cell 07: U+6227 `戧` CJK UNIFIED IDEOGRAPH-6227
- Cell 08: U+6410 `搐` CJK UNIFIED IDEOGRAPH-6410
- Cell 09: U+6473 `摳` CJK UNIFIED IDEOGRAPH-6473
- Cell 10: U+66E9 `曩` CJK UNIFIED IDEOGRAPH-66E9
- Cell 11: U+71FE `燾` CJK UNIFIED IDEOGRAPH-71FE
- Cell 12: U+750D `甍` CJK UNIFIED IDEOGRAPH-750D
- Cell 13: U+7A85 `窅` CJK UNIFIED IDEOGRAPH-7A85
- Cell 14: U+7AA8 `窨` CJK UNIFIED IDEOGRAPH-7AA8
- Cell 15: U+8401 `萁` CJK UNIFIED IDEOGRAPH-8401
- Cell 16: U+88A4 `袤` CJK UNIFIED IDEOGRAPH-88A4

Text (verbatim):
厘娉嶢彘
恂恓戧搐
摳曩燾甍
窅窨萁袤

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
