DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite',
    }
}

SQUIRRUS_URL='http://guest:guest@localhost:55670/socks-api/default'
SQUIRRUS_LOCAL_URL='http://127.0.0.1:8000/'
IDENTICA_USER=''
IDENTICA_PASS=''
