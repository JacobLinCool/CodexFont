# Image-generated Han-delta sheet dict-han-0061

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0061.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0061.png` (`0c0166a25d74607fcafabb911ecf039671cf2d6415973d670b4a1f9399a8866c`)
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
鷃亳厓叡 / 咷唄啐喁 / 嗶噘嚌囔 / 婭崒嶧巘.

Exact occupied cells:
- Cell 01: U+9DC3 `鷃` CJK UNIFIED IDEOGRAPH-9DC3
- Cell 02: U+4EB3 `亳` CJK UNIFIED IDEOGRAPH-4EB3
- Cell 03: U+5393 `厓` CJK UNIFIED IDEOGRAPH-5393
- Cell 04: U+53E1 `叡` CJK UNIFIED IDEOGRAPH-53E1
- Cell 05: U+54B7 `咷` CJK UNIFIED IDEOGRAPH-54B7
- Cell 06: U+5504 `唄` CJK UNIFIED IDEOGRAPH-5504
- Cell 07: U+5550 `啐` CJK UNIFIED IDEOGRAPH-5550
- Cell 08: U+5581 `喁` CJK UNIFIED IDEOGRAPH-5581
- Cell 09: U+55F6 `嗶` CJK UNIFIED IDEOGRAPH-55F6
- Cell 10: U+5658 `噘` CJK UNIFIED IDEOGRAPH-5658
- Cell 11: U+568C `嚌` CJK UNIFIED IDEOGRAPH-568C
- Cell 12: U+56D4 `囔` CJK UNIFIED IDEOGRAPH-56D4
- Cell 13: U+5A6D `婭` CJK UNIFIED IDEOGRAPH-5A6D
- Cell 14: U+5D12 `崒` CJK UNIFIED IDEOGRAPH-5D12
- Cell 15: U+5DA7 `嶧` CJK UNIFIED IDEOGRAPH-5DA7
- Cell 16: U+5DD8 `巘` CJK UNIFIED IDEOGRAPH-5DD8

Text (verbatim):
鷃亳厓叡
咷唄啐喁
嗶噘嚌囔
婭崒嶧巘

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
