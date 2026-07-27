# Image-generated Han-delta sheet dict-han-0005

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0005.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0005.png` (`f1b05dbb43b0c92b52e2e1b355bb3dc7f3d64bdcf374afac1a7a6ff5c6794a19`)
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
摻枷鎧丰 / 汴謾邈鄲 / 隄沓潁眇 / 鴟摶潢簌.

Exact occupied cells:
- Cell 01: U+647B `摻` CJK UNIFIED IDEOGRAPH-647B
- Cell 02: U+67B7 `枷` CJK UNIFIED IDEOGRAPH-67B7
- Cell 03: U+93A7 `鎧` CJK UNIFIED IDEOGRAPH-93A7
- Cell 04: U+4E30 `丰` CJK UNIFIED IDEOGRAPH-4E30
- Cell 05: U+6C74 `汴` CJK UNIFIED IDEOGRAPH-6C74
- Cell 06: U+8B3E `謾` CJK UNIFIED IDEOGRAPH-8B3E
- Cell 07: U+9088 `邈` CJK UNIFIED IDEOGRAPH-9088
- Cell 08: U+9132 `鄲` CJK UNIFIED IDEOGRAPH-9132
- Cell 09: U+9684 `隄` CJK UNIFIED IDEOGRAPH-9684
- Cell 10: U+6C93 `沓` CJK UNIFIED IDEOGRAPH-6C93
- Cell 11: U+6F41 `潁` CJK UNIFIED IDEOGRAPH-6F41
- Cell 12: U+7707 `眇` CJK UNIFIED IDEOGRAPH-7707
- Cell 13: U+9D1F `鴟` CJK UNIFIED IDEOGRAPH-9D1F
- Cell 14: U+6476 `摶` CJK UNIFIED IDEOGRAPH-6476
- Cell 15: U+6F62 `潢` CJK UNIFIED IDEOGRAPH-6F62
- Cell 16: U+7C0C `簌` CJK UNIFIED IDEOGRAPH-7C0C

Text (verbatim):
摻枷鎧丰
汴謾邈鄲
隄沓潁眇
鴟摶潢簌

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
