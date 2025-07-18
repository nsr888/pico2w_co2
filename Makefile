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
pull_main:
	mpremote fs cp :main.py main.py
ls:
	mpremote fs ls
pull_all:
	mpremote fs cp :main.py main.py
