# Image-generated Han-delta sheet dict-han-0066

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0066.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0066.png` (`261698a8ca1e371957f0dd0bb03f496bda6ec887e38b258665d3da2e133d0406`)
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
鯡鸕黥齠 / 喈嗩坌坳 / 媟媯崟徉 / 惙慥憒扆.

Exact occupied cells:
- Cell 01: U+9BE1 `鯡` CJK UNIFIED IDEOGRAPH-9BE1
- Cell 02: U+9E15 `鸕` CJK UNIFIED IDEOGRAPH-9E15
- Cell 03: U+9EE5 `黥` CJK UNIFIED IDEOGRAPH-9EE5
- Cell 04: U+9F60 `齠` CJK UNIFIED IDEOGRAPH-9F60
- Cell 05: U+5588 `喈` CJK UNIFIED IDEOGRAPH-5588
- Cell 06: U+55E9 `嗩` CJK UNIFIED IDEOGRAPH-55E9
- Cell 07: U+574C `坌` CJK UNIFIED IDEOGRAPH-574C
- Cell 08: U+5773 `坳` CJK UNIFIED IDEOGRAPH-5773
- Cell 09: U+5A9F `媟` CJK UNIFIED IDEOGRAPH-5A9F
- Cell 10: U+5AAF `媯` CJK UNIFIED IDEOGRAPH-5AAF
- Cell 11: U+5D1F `崟` CJK UNIFIED IDEOGRAPH-5D1F
- Cell 12: U+5F89 `徉` CJK UNIFIED IDEOGRAPH-5F89
- Cell 13: U+60D9 `惙` CJK UNIFIED IDEOGRAPH-60D9
- Cell 14: U+6165 `慥` CJK UNIFIED IDEOGRAPH-6165
- Cell 15: U+6192 `憒` CJK UNIFIED IDEOGRAPH-6192
- Cell 16: U+6246 `扆` CJK UNIFIED IDEOGRAPH-6246

Text (verbatim):
鯡鸕黥齠
喈嗩坌坳
媟媯崟徉
惙慥憒扆

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
