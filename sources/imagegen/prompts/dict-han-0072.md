# Image-generated Han-delta sheet dict-han-0072

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0072.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0072.png` (`3914367e939e78b1dab1c602f5ba95c67ad5e10710bd11deda5289ddef39ae3a`)
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
猱琬畎瘝 / 皤确稂粢 / 縶纚羧胼 / 腷艋莪蘼.

Exact occupied cells:
- Cell 01: U+7331 `猱` CJK UNIFIED IDEOGRAPH-7331
- Cell 02: U+742C `琬` CJK UNIFIED IDEOGRAPH-742C
- Cell 03: U+754E `畎` CJK UNIFIED IDEOGRAPH-754E
- Cell 04: U+761D `瘝` CJK UNIFIED IDEOGRAPH-761D
- Cell 05: U+76A4 `皤` CJK UNIFIED IDEOGRAPH-76A4
- Cell 06: U+786E `确` CJK UNIFIED IDEOGRAPH-786E
- Cell 07: U+7A02 `稂` CJK UNIFIED IDEOGRAPH-7A02
- Cell 08: U+7CA2 `粢` CJK UNIFIED IDEOGRAPH-7CA2
- Cell 09: U+7E36 `縶` CJK UNIFIED IDEOGRAPH-7E36
- Cell 10: U+7E9A `纚` CJK UNIFIED IDEOGRAPH-7E9A
- Cell 11: U+7FA7 `羧` CJK UNIFIED IDEOGRAPH-7FA7
- Cell 12: U+80FC `胼` CJK UNIFIED IDEOGRAPH-80FC
- Cell 13: U+8177 `腷` CJK UNIFIED IDEOGRAPH-8177
- Cell 14: U+824B `艋` CJK UNIFIED IDEOGRAPH-824B
- Cell 15: U+83AA `莪` CJK UNIFIED IDEOGRAPH-83AA
- Cell 16: U+863C `蘼` CJK UNIFIED IDEOGRAPH-863C

Text (verbatim):
猱琬畎瘝
皤确稂粢
縶纚羧胼
腷艋莪蘼

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
