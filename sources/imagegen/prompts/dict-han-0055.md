# Image-generated Han-delta sheet dict-han-0055

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0055.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0055.png` (`8d6c7fbb4540862f597ccb0293a8cecbe993b2e160f31d1e9d6db56094bb0032`)
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
渟湎滃濆 / 焯燔獠琛 / 琯璵畋瘻 / 癇窿篥籜.

Exact occupied cells:
- Cell 01: U+6E1F `渟` CJK UNIFIED IDEOGRAPH-6E1F
- Cell 02: U+6E4E `湎` CJK UNIFIED IDEOGRAPH-6E4E
- Cell 03: U+6EC3 `滃` CJK UNIFIED IDEOGRAPH-6EC3
- Cell 04: U+6FC6 `濆` CJK UNIFIED IDEOGRAPH-6FC6
- Cell 05: U+712F `焯` CJK UNIFIED IDEOGRAPH-712F
- Cell 06: U+71D4 `燔` CJK UNIFIED IDEOGRAPH-71D4
- Cell 07: U+7360 `獠` CJK UNIFIED IDEOGRAPH-7360
- Cell 08: U+741B `琛` CJK UNIFIED IDEOGRAPH-741B
- Cell 09: U+742F `琯` CJK UNIFIED IDEOGRAPH-742F
- Cell 10: U+74B5 `璵` CJK UNIFIED IDEOGRAPH-74B5
- Cell 11: U+754B `畋` CJK UNIFIED IDEOGRAPH-754B
- Cell 12: U+763B `瘻` CJK UNIFIED IDEOGRAPH-763B
- Cell 13: U+7647 `癇` CJK UNIFIED IDEOGRAPH-7647
- Cell 14: U+7ABF `窿` CJK UNIFIED IDEOGRAPH-7ABF
- Cell 15: U+7BE5 `篥` CJK UNIFIED IDEOGRAPH-7BE5
- Cell 16: U+7C5C `籜` CJK UNIFIED IDEOGRAPH-7C5C

Text (verbatim):
渟湎滃濆
焯燔獠琛
琯璵畋瘻
癇窿篥籜

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
