# Image-generated Han-delta sheet dict-han-0030

- Generator: built-in `image_gen`
- Generator call: `<PENDING: filled only by register>`
- Raster: `../raster/dict-han-0030.png`
- Raster SHA-256: `<PENDING: filled only by register>`
- Collection: `../collections/clear-hand-tc-dictionary-salience-1216.json` (`5623b1f977d1412b233a34c255627749ffed71f86182125ea91d7d1f1fb869c2`)
- Repertoire: `../repertoires/dictionary-salience-extension-1216.json` (`8462d9669e6d7320f77c285a444e388da0f3e0d23ae408c7212c4302bdaed840`)
- Prompt template: `../prompts/han-delta-grid-with-copybook-v1.md` (`38f8705ecdc33271d861db54ce7bb6b397ada40253052d74a916b0e1f89a3e0c`)
- Style reference: `../raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `../copybooks/dict-han-0030.png` (`c9b1060b92d1c9a7295dd1093a488e1695e7c96851a3e30ff684558090b9787a`)
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
罌罣翬葭 / 衒謅遯邛 / 邠頜餔驂 / 鶩鸛麤孃.

Exact occupied cells:
- Cell 01: U+7F4C `罌` CJK UNIFIED IDEOGRAPH-7F4C
- Cell 02: U+7F63 `罣` CJK UNIFIED IDEOGRAPH-7F63
- Cell 03: U+7FEC `翬` CJK UNIFIED IDEOGRAPH-7FEC
- Cell 04: U+846D `葭` CJK UNIFIED IDEOGRAPH-846D
- Cell 05: U+8852 `衒` CJK UNIFIED IDEOGRAPH-8852
- Cell 06: U+8B05 `謅` CJK UNIFIED IDEOGRAPH-8B05
- Cell 07: U+906F `遯` CJK UNIFIED IDEOGRAPH-906F
- Cell 08: U+909B `邛` CJK UNIFIED IDEOGRAPH-909B
- Cell 09: U+90A0 `邠` CJK UNIFIED IDEOGRAPH-90A0
- Cell 10: U+981C `頜` CJK UNIFIED IDEOGRAPH-981C
- Cell 11: U+9914 `餔` CJK UNIFIED IDEOGRAPH-9914
- Cell 12: U+9A42 `驂` CJK UNIFIED IDEOGRAPH-9A42
- Cell 13: U+9DA9 `鶩` CJK UNIFIED IDEOGRAPH-9DA9
- Cell 14: U+9E1B `鸛` CJK UNIFIED IDEOGRAPH-9E1B
- Cell 15: U+9EA4 `麤` CJK UNIFIED IDEOGRAPH-9EA4
- Cell 16: U+5B43 `孃` CJK UNIFIED IDEOGRAPH-5B43

Text (verbatim):
罌罣翬葭
衒謅遯邛
邠頜餔驂
鶩鸛麤孃

Constraints: preserve every requested Unicode identity and Taiwan Traditional
character topology; output each target exactly once and only in its assigned
cell; use complete standard strokes; keep one centered black glyph per occupied
cell with open counters; keep all ink away from separators. All sixteen cells are occupied.

Avoid: simplified variants, wrong or missing strokes, duplicate or omitted
characters, extra text, printed type, brush blobs, texture, shadows, sharp
miter spikes, thorn-like protrusions, accidental hooks, tangled cursive,
clipping, connected cells, signature, logo, or watermark.
```
