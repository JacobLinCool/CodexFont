# Image-generated Han-delta sheet dict-han-0007

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0007.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0007.png` (`15d2440105a8fe6e4d5d879fbadb22356444e0561a110b18084bd77c09451825`)
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
駰鶻冲屣 / 憋楣燼踞 / 鄴饗鬻斛 / 畿笳醮陂.

Exact occupied cells:
- Cell 01: U+99F0 `駰` CJK UNIFIED IDEOGRAPH-99F0
- Cell 02: U+9DBB `鶻` CJK UNIFIED IDEOGRAPH-9DBB
- Cell 03: U+51B2 `冲` CJK UNIFIED IDEOGRAPH-51B2
- Cell 04: U+5C63 `屣` CJK UNIFIED IDEOGRAPH-5C63
- Cell 05: U+618B `憋` CJK UNIFIED IDEOGRAPH-618B
- Cell 06: U+6963 `楣` CJK UNIFIED IDEOGRAPH-6963
- Cell 07: U+71FC `燼` CJK UNIFIED IDEOGRAPH-71FC
- Cell 08: U+8E1E `踞` CJK UNIFIED IDEOGRAPH-8E1E
- Cell 09: U+9134 `鄴` CJK UNIFIED IDEOGRAPH-9134
- Cell 10: U+9957 `饗` CJK UNIFIED IDEOGRAPH-9957
- Cell 11: U+9B3B `鬻` CJK UNIFIED IDEOGRAPH-9B3B
- Cell 12: U+659B `斛` CJK UNIFIED IDEOGRAPH-659B
- Cell 13: U+757F `畿` CJK UNIFIED IDEOGRAPH-757F
- Cell 14: U+7B33 `笳` CJK UNIFIED IDEOGRAPH-7B33
- Cell 15: U+91AE `醮` CJK UNIFIED IDEOGRAPH-91AE
- Cell 16: U+9642 `陂` CJK UNIFIED IDEOGRAPH-9642

Text (verbatim):
駰鶻冲屣
憋楣燼踞
鄴饗鬻斛
畿笳醮陂

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
