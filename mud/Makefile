run: db.sqlite
	./manage.py runserver 0.0.0.0:8000

db.sqlite:
	./manage.py syncdb --noinput
	./manage.py loaddata core/rooms.json
	@echo "Run: ./manage.py createsuperuser --username=<user> --email=a@b.co.uk"

clean:
	./manage.py dumpdata \
		--format=json \
		--indent=4 core > /tmp/backup.json
	find . -name \*pyc|xargs --no-run-if-empty rm

poll:
	while [ 1 ]; do curl http://127.0.0.1:8000/tick; echo; sleep 10; done
