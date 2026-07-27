# Image-generated Han-delta sheet dict-han-0076

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0076.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0076.png` (`877e2d6aded838c554e741983c140a6e83ea2c4eb5d25608077578dcb3e48e6e`)
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
掗攞旯昶 / 暾栱桁桉 / 楯槤櫸殂 / 洳溧滈澒.

Exact occupied cells:
- Cell 01: U+6397 `掗` CJK UNIFIED IDEOGRAPH-6397
- Cell 02: U+651E `攞` CJK UNIFIED IDEOGRAPH-651E
- Cell 03: U+65EF `旯` CJK UNIFIED IDEOGRAPH-65EF
- Cell 04: U+6636 `昶` CJK UNIFIED IDEOGRAPH-6636
- Cell 05: U+66BE `暾` CJK UNIFIED IDEOGRAPH-66BE
- Cell 06: U+6831 `栱` CJK UNIFIED IDEOGRAPH-6831
- Cell 07: U+6841 `桁` CJK UNIFIED IDEOGRAPH-6841
- Cell 08: U+6849 `桉` CJK UNIFIED IDEOGRAPH-6849
- Cell 09: U+696F `楯` CJK UNIFIED IDEOGRAPH-696F
- Cell 10: U+69E4 `槤` CJK UNIFIED IDEOGRAPH-69E4
- Cell 11: U+6AF8 `櫸` CJK UNIFIED IDEOGRAPH-6AF8
- Cell 12: U+6B82 `殂` CJK UNIFIED IDEOGRAPH-6B82
- Cell 13: U+6D33 `洳` CJK UNIFIED IDEOGRAPH-6D33
- Cell 14: U+6EA7 `溧` CJK UNIFIED IDEOGRAPH-6EA7
- Cell 15: U+6EC8 `滈` CJK UNIFIED IDEOGRAPH-6EC8
- Cell 16: U+6F92 `澒` CJK UNIFIED IDEOGRAPH-6F92

Text (verbatim):
掗攞旯昶
暾栱桁桉
楯槤櫸殂
洳溧滈澒

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
