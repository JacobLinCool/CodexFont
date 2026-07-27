# Image-generated Han-delta sheet dict-han-0041

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0041.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0041.png` (`a7c55399dae4ebc635c124579ea6d032798e6ddf13c14970ac98e250311b9b00`)
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
櫳櫺淬潞 / 烟牓痂皙 / 禰禺紺腓 / 葺蓴褡覿.

Exact occupied cells:
- Cell 01: U+6AF3 `櫳` CJK UNIFIED IDEOGRAPH-6AF3
- Cell 02: U+6AFA `櫺` CJK UNIFIED IDEOGRAPH-6AFA
- Cell 03: U+6DEC `淬` CJK UNIFIED IDEOGRAPH-6DEC
- Cell 04: U+6F5E `潞` CJK UNIFIED IDEOGRAPH-6F5E
- Cell 05: U+70DF `烟` CJK UNIFIED IDEOGRAPH-70DF
- Cell 06: U+7253 `牓` CJK UNIFIED IDEOGRAPH-7253
- Cell 07: U+75C2 `痂` CJK UNIFIED IDEOGRAPH-75C2
- Cell 08: U+7699 `皙` CJK UNIFIED IDEOGRAPH-7699
- Cell 09: U+79B0 `禰` CJK UNIFIED IDEOGRAPH-79B0
- Cell 10: U+79BA `禺` CJK UNIFIED IDEOGRAPH-79BA
- Cell 11: U+7D3A `紺` CJK UNIFIED IDEOGRAPH-7D3A
- Cell 12: U+8153 `腓` CJK UNIFIED IDEOGRAPH-8153
- Cell 13: U+847A `葺` CJK UNIFIED IDEOGRAPH-847A
- Cell 14: U+84F4 `蓴` CJK UNIFIED IDEOGRAPH-84F4
- Cell 15: U+8921 `褡` CJK UNIFIED IDEOGRAPH-8921
- Cell 16: U+89BF `覿` CJK UNIFIED IDEOGRAPH-89BF

Text (verbatim):
櫳櫺淬潞
烟牓痂皙
禰禺紺腓
葺蓴褡覿

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
