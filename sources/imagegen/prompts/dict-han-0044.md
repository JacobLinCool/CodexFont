# Image-generated Han-delta sheet dict-han-0044

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0044.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0044.png` (`53ef1934a0947b42c6cfe9bcaa28d5b3fbf8713c8924d79ffe2d407b47f22dcd`)
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
綦缾翃茯 / 莆莩蕎蛸 / 蜩螭袪褭 / 詎貺輞鋏.

Exact occupied cells:
- Cell 01: U+7DA6 `綦` CJK UNIFIED IDEOGRAPH-7DA6
- Cell 02: U+7F3E `缾` CJK UNIFIED IDEOGRAPH-7F3E
- Cell 03: U+7FC3 `翃` CJK UNIFIED IDEOGRAPH-7FC3
- Cell 04: U+832F `茯` CJK UNIFIED IDEOGRAPH-832F
- Cell 05: U+8386 `莆` CJK UNIFIED IDEOGRAPH-8386
- Cell 06: U+83A9 `莩` CJK UNIFIED IDEOGRAPH-83A9
- Cell 07: U+854E `蕎` CJK UNIFIED IDEOGRAPH-854E
- Cell 08: U+86F8 `蛸` CJK UNIFIED IDEOGRAPH-86F8
- Cell 09: U+8729 `蜩` CJK UNIFIED IDEOGRAPH-8729
- Cell 10: U+87AD `螭` CJK UNIFIED IDEOGRAPH-87AD
- Cell 11: U+88AA `袪` CJK UNIFIED IDEOGRAPH-88AA
- Cell 12: U+892D `褭` CJK UNIFIED IDEOGRAPH-892D
- Cell 13: U+8A4E `詎` CJK UNIFIED IDEOGRAPH-8A4E
- Cell 14: U+8CBA `貺` CJK UNIFIED IDEOGRAPH-8CBA
- Cell 15: U+8F1E `輞` CJK UNIFIED IDEOGRAPH-8F1E
- Cell 16: U+92CF `鋏` CJK UNIFIED IDEOGRAPH-92CF

Text (verbatim):
綦缾翃茯
莆莩蕎蛸
蜩螭袪褭
詎貺輞鋏

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
