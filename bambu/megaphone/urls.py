from django.conf.urls.defaults import patterns, include, url
from bambu.bootstrap.decorators import body_classes
from bambu.megaphone.views import *

urlpatterns = patterns('',
	url(r'^auth/$', auth, name = 'megaphone_auth'),
	url(r'^deauth/$', deauth, name = 'megaphone_deauth'),
	url(r'^callback/$', callback, name = 'megaphone_callback'),
	url(r'^t/(?P<pk>\d+)/$', track_link, name = 'megaphone_track_link'),
	url(r'profile/$', body_classes(connect, 'profile', 'profile-megaphone'), name = 'profile_connect'),
	url(r'profile/add/$',
		body_classes(connect_add_action, 'profile', 'profile-megaphone', 'profile-megaphone-edit'),
		name = 'connect_add_action'
	),
	url(r'profile/delete/$',
		body_classes(connect_delete_action, 'profile', 'profile-megaphone', 'profile-megaphone-delete'),
		name = 'connect_delete_action'
	)
)