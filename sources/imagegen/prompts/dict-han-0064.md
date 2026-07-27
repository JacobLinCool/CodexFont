# Image-generated Han-delta sheet dict-han-0064

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0064.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0064.png` (`8b9cb2b4ae4cc7a126f090577851708f3142f12f9b50e05f22a916022d193d28`)
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
腼苷茆荽 / 葯蒺蔌蕡 / 豸賸賻赬 / 踔蹡躋躓.

Exact occupied cells:
- Cell 01: U+817C `腼` CJK UNIFIED IDEOGRAPH-817C
- Cell 02: U+82F7 `苷` CJK UNIFIED IDEOGRAPH-82F7
- Cell 03: U+8306 `茆` CJK UNIFIED IDEOGRAPH-8306
- Cell 04: U+837D `荽` CJK UNIFIED IDEOGRAPH-837D
- Cell 05: U+846F `葯` CJK UNIFIED IDEOGRAPH-846F
- Cell 06: U+84BA `蒺` CJK UNIFIED IDEOGRAPH-84BA
- Cell 07: U+850C `蔌` CJK UNIFIED IDEOGRAPH-850C
- Cell 08: U+8561 `蕡` CJK UNIFIED IDEOGRAPH-8561
- Cell 09: U+8C78 `豸` CJK UNIFIED IDEOGRAPH-8C78
- Cell 10: U+8CF8 `賸` CJK UNIFIED IDEOGRAPH-8CF8
- Cell 11: U+8CFB `賻` CJK UNIFIED IDEOGRAPH-8CFB
- Cell 12: U+8D6C `赬` CJK UNIFIED IDEOGRAPH-8D6C
- Cell 13: U+8E14 `踔` CJK UNIFIED IDEOGRAPH-8E14
- Cell 14: U+8E61 `蹡` CJK UNIFIED IDEOGRAPH-8E61
- Cell 15: U+8E8B `躋` CJK UNIFIED IDEOGRAPH-8E8B
- Cell 16: U+8E93 `躓` CJK UNIFIED IDEOGRAPH-8E93

Text (verbatim):
腼苷茆荽
葯蒺蔌蕡
豸賸賻赬
踔蹡躋躓

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
