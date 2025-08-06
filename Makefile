run:
	mpremote run main.py
push:
	mpremote fs cp main.py :main.py
push_all:
	mpremote fs cp main.py :main.py
	mpremote fs cp sdcard.py :sdcard.py
	mpremote fs cp scd4x.py :scd4x.py
	mpremote fs cp ds3231.py :ds3231.py
	mpremote fs cp microdot.py :microdot.py
	mpremote fs cp -r utemplate/ :utemplate/
	mpremote fs cp -r templates/ :templates/
pull_main:
	mpremote fs cp :main.py main.py
ls:
	mpremote fs ls
pull_all:
	mpremote fs cp :main.py main.py

# HTML generation with fake data
generate-html:
	python3 generate_html.py all

preview-dashboard:
	python3 generate_html.py dashboard --open

preview-dashboard-poor:
	python3 generate_html.py dashboard --scenario poor --open

preview-dashboard-excellent:
	python3 generate_html.py dashboard --scenario excellent --open

preview-daily:
	python3 generate_html.py daily --open

preview-weekly:
	python3 generate_html.py weekly --open

clean-html:
	rm -rf html_preview/

help-html:
	@echo "HTML Generation Commands:"
	@echo "  generate-html           - Generate all HTML files with fake data"
	@echo "  preview-dashboard       - Generate and open dashboard (normal conditions)"
	@echo "  preview-dashboard-poor  - Generate and open dashboard (poor air quality)"
	@echo "  preview-dashboard-excellent - Generate and open dashboard (excellent air)"
	@echo "  preview-daily          - Generate and open daily chart"
	@echo "  preview-weekly         - Generate and open weekly chart"
	@echo "  clean-html             - Remove generated HTML files"
	@echo ""
	@echo "Original MicroPython Commands:"
	@echo "  run                    - Run main.py on MicroPython device"
	@echo "  push                   - Copy main.py to device"
	@echo "  push_all               - Copy all files to device (including templates)"
	@echo "  pull_main              - Copy main.py from device"
	@echo "  ls                     - List files on device"
