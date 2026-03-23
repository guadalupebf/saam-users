from .settings import *

ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'saam_users_01122020',
        'USER':'developer',
        'PASSWORD':'developer',
        'HOST':'localhost',
        'PORT':'',
    },
    'old_cas': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cas_01122020',
        'USER':'developer',
        'PASSWORD':'developer',
        'HOST':'localhost',
        'PORT':'',
    },
    'new_cas': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'saam_users_01122020',
        'USER':'developer',
        'PASSWORD':'developer',
        'HOST':'localhost',
        'PORT':'',
    },
    'saam': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'miurabox_01122020',
        'USER':'developer',
        'PASSWORD':'developer',
        'HOST':'localhost',
        'PORT':'',
    }
}


MEDIAFILES_LOCATION = 'cas'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'


SAAM_API_IP = "http://127.0.0.1:8000/"
MC_API_IP = "http://127.0.0.1:8001/"
OLD_SAAM_API_IP = "https://pre_api.miurabox.com/"
PAYMENT_API_IP = "http://127.0.0.1:9002/"
MAIL_SERVICE = 'http://127.0.0.1:8014/'