from django.conf.urls.defaults import *

urlpatterns = patterns('bambu.uploadify.views',
	url(r'upload/$', 'upload', name = 'uploadify_upload'),
)