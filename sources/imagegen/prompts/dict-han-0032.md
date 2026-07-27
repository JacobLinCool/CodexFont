# Image-generated Han-delta sheet dict-han-0032

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0032.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0032.png` (`88a19170016fa7608d9559ab61d1e8c551dc613d9babae93d96c829387dbae0f`)
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
蜉螽蠲裰 / 誚諶邳靚 / 饈饕鯁嘏 / 帙摛擯杪.

Exact occupied cells:
- Cell 01: U+8709 `蜉` CJK UNIFIED IDEOGRAPH-8709
- Cell 02: U+87BD `螽` CJK UNIFIED IDEOGRAPH-87BD
- Cell 03: U+8832 `蠲` CJK UNIFIED IDEOGRAPH-8832
- Cell 04: U+88F0 `裰` CJK UNIFIED IDEOGRAPH-88F0
- Cell 05: U+8A9A `誚` CJK UNIFIED IDEOGRAPH-8A9A
- Cell 06: U+8AF6 `諶` CJK UNIFIED IDEOGRAPH-8AF6
- Cell 07: U+90B3 `邳` CJK UNIFIED IDEOGRAPH-90B3
- Cell 08: U+975A `靚` CJK UNIFIED IDEOGRAPH-975A
- Cell 09: U+9948 `饈` CJK UNIFIED IDEOGRAPH-9948
- Cell 10: U+9955 `饕` CJK UNIFIED IDEOGRAPH-9955
- Cell 11: U+9BC1 `鯁` CJK UNIFIED IDEOGRAPH-9BC1
- Cell 12: U+560F `嘏` CJK UNIFIED IDEOGRAPH-560F
- Cell 13: U+5E19 `帙` CJK UNIFIED IDEOGRAPH-5E19
- Cell 14: U+645B `摛` CJK UNIFIED IDEOGRAPH-645B
- Cell 15: U+64EF `擯` CJK UNIFIED IDEOGRAPH-64EF
- Cell 16: U+676A `杪` CJK UNIFIED IDEOGRAPH-676A

Text (verbatim):
蜉螽蠲裰
誚諶邳靚
饈饕鯁嘏
帙摛擯杪

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
