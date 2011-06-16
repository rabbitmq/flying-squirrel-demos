all: venv/.ok run

venv/.ok:
	virtualenv venv
	./venv/bin/pip install django httplib2 flyingsquirrel
	rm -rf distribute-0.6.10.tar.gz
	touch venv/.ok

run: mud/db.sqlite
	cd mud && \
		./manage.py runserver 0.0.0.0:8000

mud/db.sqlite:
	cd mud && \
		./manage.py syncdb --noinput
	cd mud && \
		./manage.py loaddata core/rooms.json
	@echo "Run: ./manage.py createsuperuser --username=<user> --email=a@b.co.uk"

clean:
	cd mud && \
		./manage.py dumpdata \
			--format=json \
			--indent=4 core > /tmp/backup.json
	find . -name \*pyc|xargs --no-run-if-empty rm

poll:
	while [ 1 ]; do curl http://127.0.0.1:8000/tick; echo; sleep 10; done
