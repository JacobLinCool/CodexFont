# Image-generated Han-delta sheet dict-han-0046

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0046.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0046.png` (`745b8ec74aaae801cc0a3ab6496c274981eac23c18f8888100fb34cde1392650`)
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
檉欹毳烝 / 熠瑀睚禳 / 窬笈縟縴 / 舄荑螯觱.

Exact occupied cells:
- Cell 01: U+6A89 `檉` CJK UNIFIED IDEOGRAPH-6A89
- Cell 02: U+6B39 `欹` CJK UNIFIED IDEOGRAPH-6B39
- Cell 03: U+6BF3 `毳` CJK UNIFIED IDEOGRAPH-6BF3
- Cell 04: U+70DD `烝` CJK UNIFIED IDEOGRAPH-70DD
- Cell 05: U+71A0 `熠` CJK UNIFIED IDEOGRAPH-71A0
- Cell 06: U+7440 `瑀` CJK UNIFIED IDEOGRAPH-7440
- Cell 07: U+775A `睚` CJK UNIFIED IDEOGRAPH-775A
- Cell 08: U+79B3 `禳` CJK UNIFIED IDEOGRAPH-79B3
- Cell 09: U+7AAC `窬` CJK UNIFIED IDEOGRAPH-7AAC
- Cell 10: U+7B08 `笈` CJK UNIFIED IDEOGRAPH-7B08
- Cell 11: U+7E1F `縟` CJK UNIFIED IDEOGRAPH-7E1F
- Cell 12: U+7E34 `縴` CJK UNIFIED IDEOGRAPH-7E34
- Cell 13: U+8204 `舄` CJK UNIFIED IDEOGRAPH-8204
- Cell 14: U+8351 `荑` CJK UNIFIED IDEOGRAPH-8351
- Cell 15: U+87AF `螯` CJK UNIFIED IDEOGRAPH-87AF
- Cell 16: U+89F1 `觱` CJK UNIFIED IDEOGRAPH-89F1

Text (verbatim):
檉欹毳烝
熠瑀睚禳
窬笈縟縴
舄荑螯觱

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
