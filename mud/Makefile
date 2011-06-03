all: venv/.ok run

venv/.ok:
	virtualenv venv
	./venv/bin/pip install django
	rm -rf distribute-0.6.10.tar.gz
	touch venv/.ok

run: mud/db.sqlite
	 cd mud && \
		PYTHONPATH=~/rabbitmq-public-umbrella/flying-squirrel-python \
		./manage.py runserver 0.0.0.0:8000

mud/db.sqlite:
	 cd mud && \
		 PYTHONPATH=~/rabbitmq-public-umbrella/flying-squirrel-python \
		./manage.py syncdb --noinput
	 cd mud && \
		 PYTHONPATH=~/rabbitmq-public-umbrella/flying-squirrel-python \
		./manage.py loaddata core/rooms.json
	@echo "Run: ./manage.py createsuperuser --username=<user> --email=a@b.co.uk"

clean:
	 PYTHONPATH=~/rabbitmq-public-umbrella/flying-squirrel-python \
		./manage.py dumpdata --format=json --indent=4 > /tmp/backup.json
	find . -name \*pyc|xargs --no-run-if-empty rm
	#rm db.sqlite

poll:
	while [ 1 ]; do curl http://mmajkowski.eng.vmware.com:8000/tick; echo; sleep 10; done
