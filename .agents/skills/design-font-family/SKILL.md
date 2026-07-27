---
name: design-font-family
description: Design, extend, validate, and release an original font family from a use case, audience, examples, repertoire, and desired feeling. Use for handwriting, monospace, display, UI, accessibility, technical, multilingual, or other purpose-built typefaces when Codex must turn a brief into original raster-authored glyphs, vector outlines, OpenType behavior, independent visual approvals, deterministic builds, web specimens, and auditable release artifacts without importing reference-font outlines.
---

# Design Font Family

## Overview

Turn a font brief into an original, reproducible font release. Keep visual
references identity-only, author visible glyphs as new raster images, and admit
outlines only through explicit geometry, proof, review, and release gates.

## Start from a contract

1. Collect the intended uses, readers, writing systems, examples, personality,
   constraints, non-goals, and license.
2. Copy `assets/design-brief.template.json` into the target project and replace
   every example value.
3. Run `scripts/validate_design_brief.py <brief.json>`.
4. Stop if the use case, repertoire denominator, reference role, or license is
   ambiguous. Never begin bulk glyph generation from a mood description alone.

Read [references/brief-and-contract.md](references/brief-and-contract.md) when
turning informal examples or feelings into measurable design decisions. Read
[references/variants.md](references/variants.md) for monospace, display, UI,
accessibility, vertical, or other special-purpose branches.

## Execute the workflow

### 1. Freeze the design direction

- Define stroke model, contrast, terminals, joins, slant, proportions, spacing,
  metrics, intended sizes, and shaping behavior.
- Declare what must remain naturally irregular and what must be systematic.
- Select a representative pilot set spanning simple, dense, round, diagonal,
  counter-bearing, mark, punctuation, numeral, and script-specific forms.
- Generate and review the pilot before expanding the repertoire.

### 2. Freeze the repertoire

- Build one canonical ordered list of Unicode scalars or unencoded glyph names.
- Record normalization, Unicode version, source authority, semantic-empty
  policy, alternates, exclusions, ordering, and a sequence hash.
- Split the list into exact, non-overlapping batches. Never infer a batch's
  contents from a prompt or a generated image.
- Treat coverage as set membership, not visual fallback behavior.

### 3. Prepare references

- Use other fonts, handwriting, photographs, standards, or character databases
  only to verify identity, topology, proportions, or intended feeling.
- Record each reference's origin, license, hash when available, and permitted
  role.
- Render identity copybooks when necessary, but prohibit extraction,
  transformation, tracing, or import of reference outlines.

### 4. Author original raster batches

- Generate clean, lossless, high-resolution raster sheets from the frozen batch.
- Put one glyph in each declared cell with unambiguous row-major identity.
- Keep the background, grid, padding, polarity, and style reference stable.
- Preserve the raw generation call, exact prompt, raster, and hashes.
- Reject and regenerate the smallest failing unit; do not repair identity by
  substituting an existing font glyph.

Read [references/image-authoring.md](references/image-authoring.md) before
designing prompts, grids, copybooks, or batch sizes.

### 5. Audit before vectorization

- Verify every cell's identity, topology, stroke count or component structure,
  grid clearance, detached marks, counters, fill state, and reference role.
- Inspect reduced raster proofs at the actual intended reading sizes.
- Record a structured decision for every glyph. A successful script is not a
  visual approval.

### 6. Vectorize and harden

- Segment only the declared cell and remove the grid deterministically.
- Trace the original raster to closed paths, convert to the chosen outline
  format, and preserve authored topology.
- Recompute geometry from the emitted font, including contours, points,
  bounds, minimum edges, acute turns, counters, and edge-connected components.
- Reject spikes, micro-edges, self-intersections, degenerate contours, cropped
  ink, wrong winding, unintended bridges, and blank visible glyphs.
- Permit deterministic normalization only when the design contract names the
  affected glyph class and the source topology remains authoritative.

### 7. Review at use sizes

- Render the font, not the source image, at all contract sizes and both
  polarities.
- Review every glyph, marks in context, representative words, paragraphs,
  spacing pairs, vertical text when supported, and extreme metrics.
- Store decisions separately from build reports. Require explicit reviewer and
  approver records whose hashes pin the exact evidence.

Read [references/qa-and-release.md](references/qa-and-release.md) before
creating geometry gates, proofs, review records, or approval schemas.

### 8. Assemble OpenType behavior

- Build `.notdef`, `cmap`, metrics, names, license metadata, and required
  OpenType tables from approved inputs only.
- Implement only contract-required features such as `kern`, `mark`, `mkmk`,
  `vert`, `vrt2`, ligatures, or script-specific shaping.
- Validate the actual compiled outlines and metrics in every output format.
- For monospaced families, validate the declared fixed advance across all
  spacing glyphs while handling marks and semantic-empty glyphs explicitly.

### 9. Release reproducibly

- Produce desktop, web, license, CSS, specimen, coverage, and machine-readable
  provenance artifacts.
- Build twice into separate directories and require byte-identical inventories.
- Verify the webfont in a real browser and scan user-supplied text against the
  exact encoded repertoire.
- Publish only when all source, geometry, shaping, metadata, proof, approval,
  and reproducibility gates pass.

## Extend an existing family

- Express the request as a delta to the existing design contract.
- Freeze new repertoire ranks and batches without rewriting prior approvals.
- Reuse style references, metrics, and gates only when their hashes and
  contracts remain valid.
- Rebuild the complete release and rerun all formats, shaping, coverage, and
  browser checks. Never declare a union repertoire without proving every member.

## Stop conditions

Stop rather than guess when any of these occur:

- identity or Unicode mapping is uncertain;
- licensing or reference-outline boundaries are unclear;
- raster, vector, proof, or shaping evidence is stale;
- a visible glyph would require fallback or substitution;
- a generated batch cannot be matched exactly to the frozen sequence;
- reviewer or approver decisions would have to be inferred;
- the advertised coverage exceeds the compiled `cmap`;
- repeated builds differ.

## Project evidence

Read [references/clear-hand-tc-case-study.md](references/clear-hand-tc-case-study.md)
when applying this workflow to a large Traditional Chinese handwriting family
or when maintaining the CodexFont repository. Keep that case's counts and
thresholds out of unrelated font contracts.
