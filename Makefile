QGIS_PROFILE ?= default
QGIS_PLUGINS_DIR ?= $(HOME)/.local/share/QGIS/QGIS3/profiles/$(QGIS_PROFILE)/python/plugins
PLUGIN_NAME ?= planscape
PLUGIN_SOURCE ?= $(CURDIR)/$(PLUGIN_NAME)
PLUGIN_TARGET ?= $(QGIS_PLUGINS_DIR)/$(PLUGIN_NAME)

.PHONY: test lint install-plugin

test:
	uv run --group dev pytest -v

lint:
	uv run ruff check .

install-plugin:
	mkdir -p "$(QGIS_PLUGINS_DIR)"
	@if [ -e "$(PLUGIN_TARGET)" ] && [ ! -L "$(PLUGIN_TARGET)" ]; then \
		echo "Refusing to overwrite non-symlink: $(PLUGIN_TARGET)"; \
		exit 1; \
	fi
	ln -sfn "$(PLUGIN_SOURCE)" "$(PLUGIN_TARGET)"
	@echo "Linked $(PLUGIN_TARGET) -> $(PLUGIN_SOURCE)"
