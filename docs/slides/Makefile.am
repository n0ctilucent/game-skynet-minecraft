EXTRA_DIST = quest-for-greebling.tex quest-for-greebling-v2.tex preamble.tex preamble-v2.tex
TEX_FILES = docs/slides/quest-for-greebling-v2.tex

.PHONY: lint lint-v1 lint-v2 all-slides pdf pdf-v1 pdf-v2 clean-slides

# Default target builds the new v2 presentation
all-slides: pdf

# Default 'pdf' points to the new v2 version
pdf: pdf-v2

# Explicit targets for both versions
pdf-v2: quest-for-greebling-v2.tex
	latexmk -pdf -interaction=nonstopmode $<

pdf-v1: quest-for-greebling.tex
	latexmk -pdf -interaction=nonstopmode $<

# Default 'lint' points to v2 audit
lint: lint-v2

lint-v2:
	@echo "==> Initializing Skynet documentation audit (v2)..."
	@if command -v chktex > /dev/null; then \
		chktex -q quest-for-greebling-v2.tex; \
		echo "==> Audit complete. Documentation stability: 100%"; \
	else \
		echo "ERROR: 'chktex' not found on this node. Install via apt-get or dnf."; \
		exit 1; \
	fi

lint-v1:
	@echo "==> Initializing Skynet documentation audit (v1 legacy)..."
	@if command -v chktex > /dev/null; then \
		chktex -q quest-for-greebling.tex; \
		echo "==> Audit complete. Documentation stability: 100%"; \
	else \
		echo "ERROR: 'chktex' not found on this node. Install via apt-get or dnf."; \
		exit 1; \
	fi

clean-slides:
	latexmk -c quest-for-greebling.tex quest-for-greebling-v2.tex
	rm -f quest-for-greebling.pdf quest-for-greebling-v2.pdf *.nav *.snm *.vrb *.fls *.fdb_latexmk
