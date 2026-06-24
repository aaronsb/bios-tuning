# bios-tuning — turn a UEFI BIOS image into a browsable Obsidian knowledge graph.
#
# Quick start:  drop a BIOS image (or MSI-style .zip) into rom/  then run  `make`
# Open the result:  point Obsidian at  vault/

SHELL        := /bin/bash
PY           ?= python3
ROM_DIR      := rom
IFR_DIR      := ifr
BUILD_DIR    := build
VAULT        := vault
CATALOG      := $(BUILD_DIR)/catalog.json

UEFIEXTRACT  := tools-uefitool/build/UEFIExtract/uefiextract
IFREXTRACTOR := tools-ifrextractor/target/release/ifrextractor

.DEFAULT_GOAL := all
.PHONY: all extract parse vault tools clean realclean help

help: ## Show this help
	@echo "bios-tuning — BIOS IFR -> Obsidian graph"
	@echo
	@grep -E '^[a-z].*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort | awk -F'\t' '{printf "  \033[1m%-10s\033[0m %s\n",$$1,$$2}'
	@echo
	@echo "Usage: drop a BIOS image (or MSI .zip) into $(ROM_DIR)/  then  make"

all: extract parse vault ## Full pipeline: extract -> parse -> vault
	@echo "==> done. Open $(VAULT)/ in Obsidian."

tools: $(IFREXTRACTOR) $(UEFIEXTRACT) ## Build the extractor toolchain (clones LongSoft repos)

$(IFREXTRACTOR):
	git clone --depth 1 https://github.com/LongSoft/IFRExtractor-RS.git tools-ifrextractor
	cd tools-ifrextractor && cargo build --release

$(UEFIEXTRACT):
	git clone --depth 1 https://github.com/LongSoft/UEFITool.git tools-uefitool
	cd tools-uefitool && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --target UEFIExtract -j$$(nproc)

extract: tools ## Stage 1: unpack BIOS in rom/ and dump IFR text to ifr/
	$(PY) tools/extract_ifr.py --rom-dir $(ROM_DIR) --out $(IFR_DIR) \
	  --uefiextract $(UEFIEXTRACT) --ifrextractor $(IFREXTRACTOR)

parse: ## Stage 2: parse ifr/*.ifr.txt into build/catalog.json
	$(PY) tools/parse_ifr.py $(IFR_DIR) $(CATALOG)

vault: ## Stage 3: render build/catalog.json into the Obsidian vault/
	$(PY) tools/build_vault.py $(CATALOG) $(VAULT)

clean: ## Remove generated catalog + vault content (keeps ifr/ and rom/)
	rm -rf $(BUILD_DIR)/catalog.json $(VAULT)/params $(VAULT)/forms $(VAULT)/vars $(VAULT)/00-index $(VAULT)/Home.md

realclean: clean ## Also remove extracted IFR and unpacked firmware dumps
	rm -f $(IFR_DIR)/*.ifr.txt
	rm -rf $(ROM_DIR)/*.dump
