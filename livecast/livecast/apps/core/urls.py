from django.urls import path, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from core import views as core_views

router = routers.SimpleRouter()

urlpatterns = [
    path('access_token/', core_views.access_token)
]

urlpatterns = format_suffix_patterns(urlpatterns)
