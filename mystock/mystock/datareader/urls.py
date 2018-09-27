from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^datareader/(?P<method>\w+)/(?P<code>\w+)$', views.index, name='index'),
    url(r'^datareader/range/(?P<start>\w+)/(?P<end>\w+)$', views.range, name='range'),
    url(r'^datareader/grow_range/(?P<start>\w+)/(?P<end>\w+)$', views.grow_range, name='grow_range'),
    url(r'^datareader/max_date/(?P<start>\w+)/(?P<end>\w+)$', views.max_date, name='max_date'),
    url(r'^datareader/k_search', views.KSearchView.as_view(), name='k_search')
]
