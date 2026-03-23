from .settings_production import *

ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'users',
        'USER':'desarrollo',
        'PASSWORD': 'GPI-CAS-desarrollo$db(desarrollo)#',
        'HOST':'miurabox-prod.cjhlodxtvidw.us-west-2.rds.amazonaws.com',
       'PORT': '5432',
    },
    'old_cas': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gpicas',
        'USER':'desarrollo',
        'PASSWORD': 'GPI-CAS-desarrollo$db(desarrollo)#',
        'HOST':'miurabox-prod.cjhlodxtvidw.us-west-2.rds.amazonaws.com',
       'PORT': '5432',
    },
    'new_cas': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'users',
        'USER':'desarrollo',
        'PASSWORD': 'GPI-CAS-desarrollo$db(desarrollo)#',
        'HOST':'miurabox-prod.cjhlodxtvidw.us-west-2.rds.amazonaws.com',
       'PORT': '5432',
    },
    'saam': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'miurabox',
        'USER':'desarrollo',
        'PASSWORD': 'GPI-CAS-desarrollo$db(desarrollo)#',
        'HOST':'miurabox-prod.cjhlodxtvidw.us-west-2.rds.amazonaws.com',
       'PORT': '5432',
    }
}

