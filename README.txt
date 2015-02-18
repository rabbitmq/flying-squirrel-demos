**Repository [moved to GitHub](https://github.com/rabbitmq/flying-squirrel-demos)**.
This is a stale read-only repository.

To run the stuff locally:

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt


To run mud:

    . venv/bin/activate
    cd mud
    ln -s settings_local_devel.py settings_local.py
    ./manage.py syncdb --noinput
    ./manage.py loaddata core/rooms.json
    ./manage.py createsuperuser --username=admin --email=a@b.co.uk
    ./manage.py runserver 0.0.0.0:8000

And on the second console:

    while [ 1 ]; do curl http://127.0.0.1:8000/tick; echo; sleep 10; done

In order to save data:

    ./manage.py dumpdata \
        --format=json \
        --indent=4 core > /tmp/rooms.json

To run the channels:

   . venv/bin/activate
   cd channels
   ln -s config_local.py config.py
   python site.py

