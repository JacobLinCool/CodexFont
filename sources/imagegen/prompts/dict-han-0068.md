# Image-generated Han-delta sheet dict-han-0068

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0068.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0068.png` (`9d7e695c45ac7deb35949d509f4aee8469b81b9d88204030754dd2ad7e69db6e`)
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
犍玎瑱畬 / 睃篝膘蔞 / 蕁蚜蛺蠖 / 褌襞讌趫.

Exact occupied cells:
- Cell 01: U+728D `犍` CJK UNIFIED IDEOGRAPH-728D
- Cell 02: U+738E `玎` CJK UNIFIED IDEOGRAPH-738E
- Cell 03: U+7471 `瑱` CJK UNIFIED IDEOGRAPH-7471
- Cell 04: U+756C `畬` CJK UNIFIED IDEOGRAPH-756C
- Cell 05: U+7743 `睃` CJK UNIFIED IDEOGRAPH-7743
- Cell 06: U+7BDD `篝` CJK UNIFIED IDEOGRAPH-7BDD
- Cell 07: U+8198 `膘` CJK UNIFIED IDEOGRAPH-8198
- Cell 08: U+851E `蔞` CJK UNIFIED IDEOGRAPH-851E
- Cell 09: U+8541 `蕁` CJK UNIFIED IDEOGRAPH-8541
- Cell 10: U+869C `蚜` CJK UNIFIED IDEOGRAPH-869C
- Cell 11: U+86FA `蛺` CJK UNIFIED IDEOGRAPH-86FA
- Cell 12: U+8816 `蠖` CJK UNIFIED IDEOGRAPH-8816
- Cell 13: U+890C `褌` CJK UNIFIED IDEOGRAPH-890C
- Cell 14: U+895E `襞` CJK UNIFIED IDEOGRAPH-895E
- Cell 15: U+8B8C `讌` CJK UNIFIED IDEOGRAPH-8B8C
- Cell 16: U+8DAB `趫` CJK UNIFIED IDEOGRAPH-8DAB

Text (verbatim):
犍玎瑱畬
睃篝膘蔞
蕁蚜蛺蠖
褌襞讌趫

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
