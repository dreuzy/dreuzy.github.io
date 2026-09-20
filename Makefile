PYTHON ?= python3

.PHONY: install build check all bibliography figures cv sitemap layout serve

install:
	$(PYTHON) -m pip install -r requirements.txt

figures:
	$(PYTHON) scripts/materialize_figure_assets.py

bibliography:
	$(PYTHON) scripts/build_static_bibliography.py
	$(PYTHON) scripts/build_publications_over_time.py

cv:
	$(PYTHON) scripts/build_cv_pdf.py

sitemap:
	$(PYTHON) scripts/build_sitemap.py

layout:
	$(PYTHON) scripts/sync_shared_layout.py

build: figures bibliography cv layout sitemap

check:
	$(PYTHON) scripts/materialize_figure_assets.py --check
	$(PYTHON) scripts/build_static_bibliography.py --check
	$(PYTHON) scripts/build_publications_over_time.py --check
	$(PYTHON) scripts/build_cv_pdf.py --check
	$(PYTHON) scripts/sync_shared_layout.py --check
	$(PYTHON) scripts/build_sitemap.py --check
	$(PYTHON) scripts/check_bilingual_mirror.py
	$(PYTHON) scripts/check_local_links.py
	$(PYTHON) scripts/check_site_quality.py

all: build check

serve:
	$(PYTHON) -m http.server 8000
