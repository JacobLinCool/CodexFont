# Image-generated Han-delta sheet dict-han-0001

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0001.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0001.png` (`9c636003b36c2d8c0ef4450ffdcb4fc62e61dc95fe778a2cb7f73af6a96e3e31`)
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
〇忒烱挂 / 毬𥳑孢謔 / 杆昉諕皋 / 踰劭諛讎.

Exact occupied cells:
- Cell 01: U+3007 `〇` IDEOGRAPHIC NUMBER ZERO
- Cell 02: U+5FD2 `忒` CJK UNIFIED IDEOGRAPH-5FD2
- Cell 03: U+70F1 `烱` CJK UNIFIED IDEOGRAPH-70F1
- Cell 04: U+6302 `挂` CJK UNIFIED IDEOGRAPH-6302
- Cell 05: U+6BEC `毬` CJK UNIFIED IDEOGRAPH-6BEC
- Cell 06: U+25CD1 `𥳑` CJK UNIFIED IDEOGRAPH-25CD1
- Cell 07: U+5B62 `孢` CJK UNIFIED IDEOGRAPH-5B62
- Cell 08: U+8B14 `謔` CJK UNIFIED IDEOGRAPH-8B14
- Cell 09: U+6746 `杆` CJK UNIFIED IDEOGRAPH-6746
- Cell 10: U+6609 `昉` CJK UNIFIED IDEOGRAPH-6609
- Cell 11: U+8AD5 `諕` CJK UNIFIED IDEOGRAPH-8AD5
- Cell 12: U+768B `皋` CJK UNIFIED IDEOGRAPH-768B
- Cell 13: U+8E30 `踰` CJK UNIFIED IDEOGRAPH-8E30
- Cell 14: U+52AD `劭` CJK UNIFIED IDEOGRAPH-52AD
- Cell 15: U+8ADB `諛` CJK UNIFIED IDEOGRAPH-8ADB
- Cell 16: U+8B8E `讎` CJK UNIFIED IDEOGRAPH-8B8E

Text (verbatim):
〇忒烱挂
毬𥳑孢謔
杆昉諕皋
踰劭諛讎

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
