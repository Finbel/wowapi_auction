from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.front, name='front'),
	url(r'^update/$', views.update, name='update'),
	url(r'^look/$', views.look, name='look'),
]