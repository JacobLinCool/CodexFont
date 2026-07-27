# Image-generated vertical sheet vertical-0002

- Repertoire: `sources/imagegen/repertoires/vertical-93.json` (`5ed215e4c69fddf3561c9c4f264f4081f16e86235574f6f462d5918087c74786`)
- Style reference: `sources/imagegen/raster/common-0001.png` (`2a4058fdb4e35ce2789f9ae73535542f78f4e94516ad4b9929986a93e36d3d81`)
- Identity copybook: `sources/imagegen/copybooks/vertical-0002.png` (`bea5ea0eae1f8d49ece62793f4615bf6a09349ec6cdd9f9cbcf6d2ec8a5db12b`)
- State: awaiting generation

## Exact tool prompt

```text
Use case: font-source raster sheet
Asset type: high-resolution 4×4 raster master sheet for original vertical-writing alternates in the Clear Hand TC family

Input images:
1. Image 1 is STYLE ONLY. Match its fine black gel-pen weight, rounded terminals, controlled handwritten rhythm, white background, and faint 4×4 grid. Do not copy its Han characters.
2. Image 2 is IDENTITY REFERENCE ONLY. Each cell shows the intended vertical-writing form using neutral reference fonts or a reference-only orientation transform. Never trace or import its printed outlines.

Draw exactly 16 independently authored vertical alternate glyphs in strict row-major order. These are new unencoded `.vert` glyphs, not mechanically rotated copies of the horizontal Clear Hand TC glyphs. Redraw each form naturally for vertical typography.

Critical orientation rule: every LEFT/RIGHT bracket or delimiter must use the TOP/BOTTOM vertical form visibly shown in Image 2. The opening left form becomes a top form opening downward; the closing right form becomes a bottom form opening upward. For example, `〈` must become `∧` and `〉` must become `∨`. Never retain a sideways `<`, `>`, `(`, `)`, `「`, `」`, or other left/right bracket silhouette in the output.

Exact occupied cells:
- Cell 01: `U+3008` LEFT ANGLE BRACKET — base `〈` — alternate `uni3008.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 02: `U+3009` RIGHT ANGLE BRACKET — base `〉` — alternate `uni3009.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 03: `U+300A` LEFT DOUBLE ANGLE BRACKET — base `《` — alternate `uni300A.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 04: `U+300B` RIGHT DOUBLE ANGLE BRACKET — base `》` — alternate `uni300B.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 05: `U+300C` LEFT CORNER BRACKET — base `「` — alternate `uni300C.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a `┐` silhouette with one top horizontal and one right downstroke; do not add a left downstroke or make a three-sided cap.
- Cell 06: `U+300D` RIGHT CORNER BRACKET — base `」` — alternate `uni300D.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a `└` silhouette with one left upstroke and one bottom horizontal; do not add a right upstroke or make a three-sided cup.
- Cell 07: `U+300E` LEFT WHITE CORNER BRACKET — base `『` — alternate `uni300E.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw two nested `┐` strokes only; do not add any left downstroke.
- Cell 08: `U+300F` RIGHT WHITE CORNER BRACKET — base `』` — alternate `uni300F.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw two nested `└` strokes only; do not add any right upstroke.
- Cell 09: `U+3010` LEFT BLACK LENTICULAR BRACKET — base `【` — alternate `uni3010.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 10: `U+3011` RIGHT BLACK LENTICULAR BRACKET — base `】` — alternate `uni3011.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 11: `U+3014` LEFT TORTOISE SHELL BRACKET — base `〔` — alternate `uni3014.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a top trapezoid bracket opening downward, with one horizontal top and two short diagonal sides; never draw a sideways C shape.
- Cell 12: `U+3015` RIGHT TORTOISE SHELL BRACKET — base `〕` — alternate `uni3015.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw a bottom trapezoid bracket opening upward, with one horizontal bottom and two short diagonal sides; never draw a backwards C shape.
- Cell 13: `U+3016` LEFT WHITE LENTICULAR BRACKET — base `〖` — alternate `uni3016.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 14: `U+3017` RIGHT WHITE LENTICULAR BRACKET — base `〗` — alternate `uni3017.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback.
- Cell 15: `U+3018` LEFT WHITE TORTOISE SHELL BRACKET — base `〘` — alternate `uni3018.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the outlined top tortoise-shell form opening downward, not a sideways left bracket.
- Cell 16: `U+3019` RIGHT WHITE TORTOISE SHELL BRACKET — base `〙` — alternate `uni3019.vert` — VO `Tr` — Unicode typographic vertical transform with rotated fallback; draw the outlined bottom tortoise-shell form opening upward, not a sideways right bracket.

Unused cells: none.

Composition: square image; four equal rows and columns; generous outer margin; faint thin light-gray separators; one centered black target in each occupied cell. Pure white background, no texture, shadow, labels, captions, Unicode text, logos, or watermarks.

Preserve exact identity, direction, topology, dot/line count, paired bracket distinction, small-kana distinction, and punctuation position. Avoid typeset stiffness, brush blobs, sharp miter spikes, thorn protrusions, clipping, duplicate/missing/reordered glyphs, connected cells, or any visible mark in unused cells.
```
