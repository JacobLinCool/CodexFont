# Image-generated Han-delta sheet dict-han-0062

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0062.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0062.png` (`14da06c8d1733d6ca9a5e27f5de912f363ba1a4dcb3098d82a87dc2abc3460a1`)
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
帔愬搨擗 / 攮杈桄梏 / 槭樛櫨沴 / 洮洹涑淖.

Exact occupied cells:
- Cell 01: U+5E14 `帔` CJK UNIFIED IDEOGRAPH-5E14
- Cell 02: U+612C `愬` CJK UNIFIED IDEOGRAPH-612C
- Cell 03: U+6428 `搨` CJK UNIFIED IDEOGRAPH-6428
- Cell 04: U+64D7 `擗` CJK UNIFIED IDEOGRAPH-64D7
- Cell 05: U+652E `攮` CJK UNIFIED IDEOGRAPH-652E
- Cell 06: U+6748 `杈` CJK UNIFIED IDEOGRAPH-6748
- Cell 07: U+6844 `桄` CJK UNIFIED IDEOGRAPH-6844
- Cell 08: U+688F `梏` CJK UNIFIED IDEOGRAPH-688F
- Cell 09: U+69ED `槭` CJK UNIFIED IDEOGRAPH-69ED
- Cell 10: U+6A1B `樛` CJK UNIFIED IDEOGRAPH-6A1B
- Cell 11: U+6AE8 `櫨` CJK UNIFIED IDEOGRAPH-6AE8
- Cell 12: U+6CB4 `沴` CJK UNIFIED IDEOGRAPH-6CB4
- Cell 13: U+6D2E `洮` CJK UNIFIED IDEOGRAPH-6D2E
- Cell 14: U+6D39 `洹` CJK UNIFIED IDEOGRAPH-6D39
- Cell 15: U+6D91 `涑` CJK UNIFIED IDEOGRAPH-6D91
- Cell 16: U+6DD6 `淖` CJK UNIFIED IDEOGRAPH-6DD6

Text (verbatim):
帔愬搨擗
攮杈桄梏
槭樛櫨沴
洮洹涑淖

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
