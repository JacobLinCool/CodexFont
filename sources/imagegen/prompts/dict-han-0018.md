# Image-generated Han-delta sheet dict-han-0018

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0018.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0018.png` (`d10cfba3d23cbf21928c0164c6fa6bf6c9b083d7fda8f43c57f3672a76b3d1bb`)
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
覈鑊喏悒 / 惇擿柢檐 / 汛瓚菖薊 / 蜒攧旆淥.

Exact occupied cells:
- Cell 01: U+8988 `覈` CJK UNIFIED IDEOGRAPH-8988
- Cell 02: U+944A `鑊` CJK UNIFIED IDEOGRAPH-944A
- Cell 03: U+558F `喏` CJK UNIFIED IDEOGRAPH-558F
- Cell 04: U+6092 `悒` CJK UNIFIED IDEOGRAPH-6092
- Cell 05: U+60C7 `惇` CJK UNIFIED IDEOGRAPH-60C7
- Cell 06: U+64FF `擿` CJK UNIFIED IDEOGRAPH-64FF
- Cell 07: U+67E2 `柢` CJK UNIFIED IDEOGRAPH-67E2
- Cell 08: U+6A90 `檐` CJK UNIFIED IDEOGRAPH-6A90
- Cell 09: U+6C5B `汛` CJK UNIFIED IDEOGRAPH-6C5B
- Cell 10: U+74DA `瓚` CJK UNIFIED IDEOGRAPH-74DA
- Cell 11: U+83D6 `菖` CJK UNIFIED IDEOGRAPH-83D6
- Cell 12: U+858A `薊` CJK UNIFIED IDEOGRAPH-858A
- Cell 13: U+8712 `蜒` CJK UNIFIED IDEOGRAPH-8712
- Cell 14: U+6527 `攧` CJK UNIFIED IDEOGRAPH-6527
- Cell 15: U+65C6 `旆` CJK UNIFIED IDEOGRAPH-65C6
- Cell 16: U+6DE5 `淥` CJK UNIFIED IDEOGRAPH-6DE5

Text (verbatim):
覈鑊喏悒
惇擿柢檐
汛瓚菖薊
蜒攧旆淥

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
