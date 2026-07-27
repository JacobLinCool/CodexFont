# Image-generated Han-delta sheet dict-han-0047

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0047.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0047.png` (`bcc10fffb93ef6c036afe9817be754105f449cdd3346bd64125d82dd9b6f010c`)
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
詈詒誆譖 / 跗躕酯醅 / 頫顴鯤鵷 / 鷸黌黼侄.

Exact occupied cells:
- Cell 01: U+8A48 `詈` CJK UNIFIED IDEOGRAPH-8A48
- Cell 02: U+8A52 `詒` CJK UNIFIED IDEOGRAPH-8A52
- Cell 03: U+8A86 `誆` CJK UNIFIED IDEOGRAPH-8A86
- Cell 04: U+8B56 `譖` CJK UNIFIED IDEOGRAPH-8B56
- Cell 05: U+8DD7 `跗` CJK UNIFIED IDEOGRAPH-8DD7
- Cell 06: U+8E95 `躕` CJK UNIFIED IDEOGRAPH-8E95
- Cell 07: U+916F `酯` CJK UNIFIED IDEOGRAPH-916F
- Cell 08: U+9185 `醅` CJK UNIFIED IDEOGRAPH-9185
- Cell 09: U+982B `頫` CJK UNIFIED IDEOGRAPH-982B
- Cell 10: U+9874 `顴` CJK UNIFIED IDEOGRAPH-9874
- Cell 11: U+9BE4 `鯤` CJK UNIFIED IDEOGRAPH-9BE4
- Cell 12: U+9D77 `鵷` CJK UNIFIED IDEOGRAPH-9D77
- Cell 13: U+9DF8 `鷸` CJK UNIFIED IDEOGRAPH-9DF8
- Cell 14: U+9ECC `黌` CJK UNIFIED IDEOGRAPH-9ECC
- Cell 15: U+9EFC `黼` CJK UNIFIED IDEOGRAPH-9EFC
- Cell 16: U+4F84 `侄` CJK UNIFIED IDEOGRAPH-4F84

Text (verbatim):
詈詒誆譖
跗躕酯醅
頫顴鯤鵷
鷸黌黼侄

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
