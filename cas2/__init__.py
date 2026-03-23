from __future__ import absolute_import, unicode_literals

from .celery import app as celery_app

# Esto sirve para que la aplicación de Celery se creé siempre
# que Django se inicie.


__all__ = ('celery_app', )
