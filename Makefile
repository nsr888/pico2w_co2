run:
	mpremote run main.py
push:
	mpremote fs cp main.py :main.py

# Template compilation
compile:
	python3 compile_templates.py
push_all: compile
	mpremote fs cp main.py :main.py
	mpremote fs cp sdcard.py :sdcard.py
	mpremote fs cp scd4x.py :scd4x.py
	mpremote fs cp ds3231.py :ds3231.py
	mpremote fs cp microdot.py :microdot.py
	mpremote fs cp utemplate/compiled.py :utemplate/compiled.py
	mpremote fs cp utemplate/recompile.py :utemplate/recompile.py
	mpremote fs cp utemplate/source.py :utemplate/source.py
	mpremote fs cp templates/index.tpl :templates/index.tpl
	mpremote fs cp templates/index_tpl.py :templates/index_tpl.py
	mpremote fs cp templates/chart.tpl :templates/chart.tpl
	mpremote fs cp templates/chart_tpl.py :templates/chart_tpl.py
	mpremote fs cp templates/base.tpl :templates/base.tpl
pull_main:
	mpremote fs cp :main.py main.py
ls:
	mpremote fs ls
pull_all:
	mpremote fs cp :main.py main.py

# HTML generation with fake data
generate-html: compile
	python3 generate_html.py all

preview-dashboard: compile
	python3 generate_html.py dashboard --open

preview-dashboard-poor: compile
	python3 generate_html.py dashboard --scenario poor --open

preview-dashboard-excellent: compile
	python3 generate_html.py dashboard --scenario excellent --open

preview-daily: compile
	python3 generate_html.py daily --open

preview-weekly: compile
	python3 generate_html.py weekly --open

clean-html:
	rm -rf html_preview/

help-html:
	@echo "HTML Generation Commands:"
	@echo "  compile                - Compile .tpl templates to _tpl.py files"
	@echo "  generate-html          - Generate all HTML files with fake data (auto-compiles)"
	@echo "  preview-dashboard      - Generate and open dashboard (normal conditions)"
	@echo "  preview-dashboard-poor - Generate and open dashboard (poor air quality)"
	@echo "  preview-dashboard-excellent - Generate and open dashboard (excellent air)"
	@echo "  preview-daily          - Generate and open daily chart"
	@echo "  preview-weekly         - Generate and open weekly chart"
	@echo "  clean-html             - Remove generated HTML files"
	@echo ""
	@echo "MicroPython Commands:"
	@echo "  run                    - Run main.py on MicroPython device"
	@echo "  push                   - Copy main.py to device"
	@echo "  push_all               - Copy all files to device (auto-compiles templates)"
	@echo "  pull_main              - Copy main.py from device"
	@echo "  ls                     - List files on device"
