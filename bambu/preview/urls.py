from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('bambu.preview.views',
	url(r'^(?P<pk>\d+)/$', 'preview', name = 'preview')
)