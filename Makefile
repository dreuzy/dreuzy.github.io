PYTHON ?= python3

.PHONY: install build check all bibliography content figures visuals cv sitemap layout serve

install:
	$(PYTHON) -m pip install -r requirements.txt

figures:
	$(PYTHON) scripts/materialize_figure_assets.py

visuals:
	$(PYTHON) scripts/build_visual_assets.py

bibliography:
	$(PYTHON) scripts/build_static_bibliography.py
	$(PYTHON) scripts/build_publications_over_time.py

content:
	$(PYTHON) scripts/build_curated_content.py

cv:
	$(PYTHON) scripts/build_cv_pdf.py

sitemap:
	$(PYTHON) scripts/build_sitemap.py

layout:
	$(PYTHON) scripts/sync_shared_layout.py

build: visuals figures content bibliography cv layout sitemap

check:
	$(PYTHON) scripts/build_visual_assets.py --check
	$(PYTHON) scripts/check_media_assets.py
	$(PYTHON) scripts/materialize_figure_assets.py --check
	$(PYTHON) scripts/build_curated_content.py --check
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
