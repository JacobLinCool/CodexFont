# Image-generated Han-delta sheet dict-han-0009

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0009.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0009.png` (`92f21b2a58cd07727806612b820141664cc8bf0bc28f4b169374ac87ef1f887a`)
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
紆圜坯夯 / 槊粘頎宕 / 幡惲懨拊 / 籙胺脛郢.

Exact occupied cells:
- Cell 01: U+7D06 `紆` CJK UNIFIED IDEOGRAPH-7D06
- Cell 02: U+571C `圜` CJK UNIFIED IDEOGRAPH-571C
- Cell 03: U+576F `坯` CJK UNIFIED IDEOGRAPH-576F
- Cell 04: U+592F `夯` CJK UNIFIED IDEOGRAPH-592F
- Cell 05: U+69CA `槊` CJK UNIFIED IDEOGRAPH-69CA
- Cell 06: U+7C98 `粘` CJK UNIFIED IDEOGRAPH-7C98
- Cell 07: U+980E `頎` CJK UNIFIED IDEOGRAPH-980E
- Cell 08: U+5B95 `宕` CJK UNIFIED IDEOGRAPH-5B95
- Cell 09: U+5E61 `幡` CJK UNIFIED IDEOGRAPH-5E61
- Cell 10: U+60F2 `惲` CJK UNIFIED IDEOGRAPH-60F2
- Cell 11: U+61E8 `懨` CJK UNIFIED IDEOGRAPH-61E8
- Cell 12: U+62CA `拊` CJK UNIFIED IDEOGRAPH-62CA
- Cell 13: U+7C59 `籙` CJK UNIFIED IDEOGRAPH-7C59
- Cell 14: U+80FA `胺` CJK UNIFIED IDEOGRAPH-80FA
- Cell 15: U+811B `脛` CJK UNIFIED IDEOGRAPH-811B
- Cell 16: U+90E2 `郢` CJK UNIFIED IDEOGRAPH-90E2

Text (verbatim):
紆圜坯夯
槊粘頎宕
幡惲懨拊
籙胺脛郢

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
