# Image-generated Han-delta sheet dict-han-0067

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0067.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0067.png` (`69c048eb90b3bb82e7d160345c66e91088b0192ad7ae778f07b3f869b5cd0026`)
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
挲掊摜撝 / 擫斌曛杠 / 桎棨楦櫬 / 沏泝瀁煒.

Exact occupied cells:
- Cell 01: U+6332 `挲` CJK UNIFIED IDEOGRAPH-6332
- Cell 02: U+638A `掊` CJK UNIFIED IDEOGRAPH-638A
- Cell 03: U+645C `摜` CJK UNIFIED IDEOGRAPH-645C
- Cell 04: U+649D `撝` CJK UNIFIED IDEOGRAPH-649D
- Cell 05: U+64EB `擫` CJK UNIFIED IDEOGRAPH-64EB
- Cell 06: U+658C `斌` CJK UNIFIED IDEOGRAPH-658C
- Cell 07: U+66DB `曛` CJK UNIFIED IDEOGRAPH-66DB
- Cell 08: U+6760 `杠` CJK UNIFIED IDEOGRAPH-6760
- Cell 09: U+684E `桎` CJK UNIFIED IDEOGRAPH-684E
- Cell 10: U+68E8 `棨` CJK UNIFIED IDEOGRAPH-68E8
- Cell 11: U+6966 `楦` CJK UNIFIED IDEOGRAPH-6966
- Cell 12: U+6AEC `櫬` CJK UNIFIED IDEOGRAPH-6AEC
- Cell 13: U+6C8F `沏` CJK UNIFIED IDEOGRAPH-6C8F
- Cell 14: U+6CDD `泝` CJK UNIFIED IDEOGRAPH-6CDD
- Cell 15: U+7001 `瀁` CJK UNIFIED IDEOGRAPH-7001
- Cell 16: U+7152 `煒` CJK UNIFIED IDEOGRAPH-7152

Text (verbatim):
挲掊摜撝
擫斌曛杠
桎棨楦櫬
沏泝瀁煒

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
