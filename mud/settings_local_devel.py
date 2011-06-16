DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite',
    }
}

## Url of a valid flyingsquirrel instance.
SQUIRRUS_URL='http://guest:guest@localhost:55670/socks-api/default'
## Url flyingsquirrel will callback.
SQUIRRUS_LOCAL_URL='http://127.0.0.1:8000/'

## Identica credentials for 'Bird' mob.
IDENTICA_USER=''
IDENTICA_PASS=''
