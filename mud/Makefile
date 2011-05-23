all: venv/.ok run

venv/.ok:
	virtualenv venv
	./venv/bin/pip install web.py
	touch venv/.ok

run:
	PYTHONPATH=~/rabbitmq-public-umbrella/flying-squirrel-python ./venv/bin/python site.py            


clean::
	rm -rf distribute-0.6.10.tar.gz venv
	find . -name \*pyc|xargs --no-run-if-empty rm

