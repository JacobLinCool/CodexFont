# Imagegen release approvals

This directory is the only admission list for the Clear Hand TC 0.1 Preview.
A raster, successful vector build, or visual-review record is not an
approval by itself.

The release contains five independently validated approval collections:

| Collection | Approval names | Required count | Encoded glyphs |
| --- | --- | ---: | ---: |
| Common Han | `common-0001.approval.json`–`common-0188.approval.json` | 188 | 3,000 |
| MOE common extension | `moe-common-extension.approval.json` | 1 | 1,844 |
| Dictionary-salience extension | `dictionary-salience-extension-1216.approval.json` | 1 | 1,216 |
| Non-Han | `nonhan-0001.approval.json`–`nonhan-0206.approval.json` | 206 | 3,060 |
| Vertical alternates | `vertical-0001.approval.json`–`vertical-0006.approval.json` | 6 | 0 |

`nonhan-0206` is the semantic-empty batch. The six vertical batches provide
93 unencoded glyphs reached through the `vert` and `vrt2` OpenType features.

Every approval is immutable and SHA-256-pinned to its frozen repertoire,
source descriptor or semantic specification, generated raster where
applicable, vector build, proof files, per-glyph review, and separate release
authorization. The validators reject unknown keys, stale hashes,
non-canonical paths, unsupported pipeline versions, missing batches, and
foreign JSON files.

## Record and authorize a visible batch

Only run these commands after inspecting every glyph at 12, 16, 20, 32, and
56 px in both polarities.

For a Han batch:

```sh
uv run python -m scripts.record_imagegen_approval record-review \
  --batch common-NNNN \
  --reviewer-name "<reviewer identity>" \
  --reviewer-role "<reviewer role>" \
  --reviewed-at "YYYY-MM-DDTHH:MM:SSZ" \
  --confirmation \
  I_REVIEWED_EVERY_GLYPH_AT_12_16_20_32_56_PX_IN_BOTH_POLARITIES

uv run python -m scripts.record_imagegen_approval authorize \
  --batch common-NNNN \
  --approver-name "<approver identity>" \
  --approved-at "YYYY-MM-DDTHH:MM:SSZ" \
  --confirmation \
  I_AUTHORIZE_THIS_HASH_PINNED_BATCH_FOR_THE_RELEASE_FONT
```

For a visible non-Han batch:

```sh
uv run python -m scripts.record_imagegen_nonhan_approval record-review \
  --batch nonhan-NNNN \
  --reviewer-name "<reviewer identity>" \
  --reviewer-role "<reviewer role>" \
  --reviewed-at "YYYY-MM-DDTHH:MM:SSZ" \
  --confirmation \
  I_REVIEWED_EVERY_NONHAN_GLYPH_AT_12_16_20_32_56_PX_IN_BOTH_POLARITIES

uv run python -m scripts.record_imagegen_nonhan_approval authorize \
  --batch nonhan-NNNN \
  --approver-name "<approver identity>" \
  --approved-at "YYYY-MM-DDTHH:MM:SSZ" \
  --confirmation \
  I_AUTHORIZE_THIS_HASH_PINNED_NONHAN_BATCH_FOR_THE_RELEASE_FONT
```

The semantic-empty and vertical recorders use different, purpose-specific
attestations. Read their exact tokens from:

```sh
uv run python -m scripts.record_imagegen_nonhan_approval record-review --help
uv run python -m scripts.record_imagegen_vertical_approval --help
```

## Validate the complete release admission set

```sh
uv run python -m scripts.imagegen_approval validate-prefix --summary
uv run python -m scripts.imagegen_nonhan_approval validate-complete
uv run python -m scripts.imagegen_vertical_approval validate-complete
```

Build only after all three commands succeed:

```sh
make release-9120
make dist
```

The release compiler independently re-hashes and reopens the approved
evidence and generated fonts. It does not read the experimental authored
source manifest or any fallback font.
