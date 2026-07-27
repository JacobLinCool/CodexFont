# Image-generated Han-delta sheet dict-han-0053

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0053.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0053.png` (`2ee3a8519e2c2c6d9160bae8243f6dbd5242222054cced08670e91b32197f23c`)
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
邶郿酲鉏 / 鑷闞雒騭 / 魍魎鯢齏 / 价倬傜唼.

Exact occupied cells:
- Cell 01: U+90B6 `邶` CJK UNIFIED IDEOGRAPH-90B6
- Cell 02: U+90FF `郿` CJK UNIFIED IDEOGRAPH-90FF
- Cell 03: U+9172 `酲` CJK UNIFIED IDEOGRAPH-9172
- Cell 04: U+924F `鉏` CJK UNIFIED IDEOGRAPH-924F
- Cell 05: U+9477 `鑷` CJK UNIFIED IDEOGRAPH-9477
- Cell 06: U+95DE `闞` CJK UNIFIED IDEOGRAPH-95DE
- Cell 07: U+96D2 `雒` CJK UNIFIED IDEOGRAPH-96D2
- Cell 08: U+9A2D `騭` CJK UNIFIED IDEOGRAPH-9A2D
- Cell 09: U+9B4D `魍` CJK UNIFIED IDEOGRAPH-9B4D
- Cell 10: U+9B4E `魎` CJK UNIFIED IDEOGRAPH-9B4E
- Cell 11: U+9BE2 `鯢` CJK UNIFIED IDEOGRAPH-9BE2
- Cell 12: U+9F4F `齏` CJK UNIFIED IDEOGRAPH-9F4F
- Cell 13: U+4EF7 `价` CJK UNIFIED IDEOGRAPH-4EF7
- Cell 14: U+502C `倬` CJK UNIFIED IDEOGRAPH-502C
- Cell 15: U+509C `傜` CJK UNIFIED IDEOGRAPH-509C
- Cell 16: U+553C `唼` CJK UNIFIED IDEOGRAPH-553C

Text (verbatim):
邶郿酲鉏
鑷闞雒騭
魍魎鯢齏
价倬傜唼

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
