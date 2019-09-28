# flake8: noqa
import MySQLdb  # noqa: F401

from livecast.settings.base import *  # noqa: F403

# from kombu import Exchange, Queue

DEBUG = True
ALLOWED_HOSTS = ['*']

# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }
# END CACHE CONFIGURATION

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'qlive',
        'USER': 'root',
        'PASSWORD': 'fenfen',
        'HOST': '139.224.212.27',
        'PORT': '3306',
        'OPTIONS': {
            # mysql < 5.7 [storage_engine], mysql >= 5.7 [default_storage_engine]
            'init_command': 'SET default_storage_engine=InnoDB',
            'sql_mode': 'STRICT_TRANS_TABLES',
            'charset': 'utf8mb4'
        }
    }
}
# END DATABASE CONFIGURATION

# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# END EMAIL CONFIGURATION

# Determine which requests should render Django Debug Toolbar
INTERNAL_IPS = ('127.0.0.1', )

ENABLE_AUTO_AUTH = True

# Setting logging level
LOGGING['handlers']['default']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'

# settings for cronjobs
CRONTAB_DJANGO_SETTINGS_MODULE = 'livecast.settings.dev'
