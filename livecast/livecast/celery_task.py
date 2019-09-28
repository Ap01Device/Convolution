# -*- coding: utf-8 -*-
# @Author  : itswcg
# @File    : celery_task.py
# @Time    : 19-4-10 下午8:18
# @Blog    : https://blog.itswcg.com
# @github  : https://github.com/itswcg

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, platforms

import django
from django.conf import settings

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'livecast.settings.dev')

django.setup()
platforms.C_FORCE_ROOT = True

app = Celery('livecast')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
