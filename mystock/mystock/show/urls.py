from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^show/line/volume/(?P<start>[^/]+)/(?P<end>\w+)/(?P<code>\w+)$', views.line_with_min_volume, name='range'),
]
