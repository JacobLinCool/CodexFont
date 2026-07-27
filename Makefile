.PHONY: all validate-imagegen validate-mew-note release-clear-hand \
	release-mew-note release-preview dist-clear-hand dist-mew-note dist \
	reproducibility site hygiene test

export UV_CACHE_DIR ?= $(CURDIR)/build/cache/uv

all: dist test

validate-imagegen:
	uv run python -m scripts.imagegen_approval validate-prefix --summary
	uv run python -m scripts.moe_common_approval validate
	uv run python -m scripts.han_delta_approval validate
	uv run python -m scripts.imagegen_nonhan_approval validate-complete
	uv run python -m scripts.imagegen_vertical_approval validate-complete

release-clear-hand: validate-imagegen
	uv run python -m scripts.build_imagegen_release_font \
		--output build/imagegen/release-9120

validate-mew-note:
	uv run python -m scripts.mew_note_release_approval validate

release-mew-note:
	uv run python -m scripts.build_mew_note_release_font \
		--output build/families/mew-note-tc/release-9088

release-preview: release-clear-hand release-mew-note

dist-clear-hand: validate-imagegen
	uv run python -m scripts.build_imagegen_release_font \
		--output dist/clear-hand-tc

dist-mew-note:
	uv run python -m scripts.build_mew_note_release_font \
		--output dist/mew-note-tc

dist: dist-clear-hand dist-mew-note

reproducibility: dist release-preview
	uv run python -m scripts.verify_release_reproducibility

hygiene:
	uv run python -m scripts.repository_hygiene

site:
	uv run python -m scripts.build_site

test:
	uv run pytest -q
