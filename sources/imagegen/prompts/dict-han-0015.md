# Image-generated Han-delta sheet dict-han-0015

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0015.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0015.png` (`bf503ff281668d6011c42ae42ebe3e68a8c1d4e6e8dd782dbfcccd99b6e488bf`)
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
褊誹孛巉 / 搥杼翫遒 / 鼂僉愷慳 / 掂栖灞璫.

Exact occupied cells:
- Cell 01: U+890A `褊` CJK UNIFIED IDEOGRAPH-890A
- Cell 02: U+8AB9 `誹` CJK UNIFIED IDEOGRAPH-8AB9
- Cell 03: U+5B5B `孛` CJK UNIFIED IDEOGRAPH-5B5B
- Cell 04: U+5DC9 `巉` CJK UNIFIED IDEOGRAPH-5DC9
- Cell 05: U+6425 `搥` CJK UNIFIED IDEOGRAPH-6425
- Cell 06: U+677C `杼` CJK UNIFIED IDEOGRAPH-677C
- Cell 07: U+7FEB `翫` CJK UNIFIED IDEOGRAPH-7FEB
- Cell 08: U+9052 `遒` CJK UNIFIED IDEOGRAPH-9052
- Cell 09: U+9F02 `鼂` CJK UNIFIED IDEOGRAPH-9F02
- Cell 10: U+50C9 `僉` CJK UNIFIED IDEOGRAPH-50C9
- Cell 11: U+6137 `愷` CJK UNIFIED IDEOGRAPH-6137
- Cell 12: U+6173 `慳` CJK UNIFIED IDEOGRAPH-6173
- Cell 13: U+6382 `掂` CJK UNIFIED IDEOGRAPH-6382
- Cell 14: U+6816 `栖` CJK UNIFIED IDEOGRAPH-6816
- Cell 15: U+705E `灞` CJK UNIFIED IDEOGRAPH-705E
- Cell 16: U+74AB `璫` CJK UNIFIED IDEOGRAPH-74AB

Text (verbatim):
褊誹孛巉
搥杼翫遒
鼂僉愷慳
掂栖灞璫

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
