# Imagegen vector visual reviews

A vector build is still `unreviewed` even when all automated checks pass.
Before a batch can be admitted, a reviewer must inspect its actual emitted
outlines/proofs and write `common-NNNN.vector-review.json`.

The strict executable schema is in `scripts/imagegen_approval.py`. The record
must:

- be `approved`, with a real reviewer identity and canonical UTC timestamp;
- pin the exact v2 vector report by path and SHA-256;
- declare all six required review checks in the prescribed order;
- cover 12, 16, 20, 32, and 56 px and both color polarities;
- pin and pass the black-on-white, white-on-black, and segmented-source proofs;
- contain one ordered `PASS` decision for every frozen batch glyph; and
- summarize all glyphs passed with zero rejects.

This directory intentionally contains no review records yet. Automated tools
must not invent reviewer identity, decisions, notes, or timestamps.
