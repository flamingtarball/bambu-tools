from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from bambu.bootstrap.decorators import body_classes
from bambu.saas.views import *
from django.contrib.auth.views import login, logout

urlpatterns = patterns('',
	url(r'^plans/$', body_classes(plans, 'saas-plans'), name = 'plans'),
	url(r'^upgrade/$', body_classes(upgrade, 'saas-upgrade'), name = 'upgrade'),
	url(r'^signup/$', body_classes(signup, 'saas-signup'), name = 'signup'),
	url(r'^signup/pay/$', body_classes(signup_pay, 'saas-signup', 'saas-signup-pay'),
		name = 'signup_pay'
	),
	url(r'^verify/(?P<guid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/$',
		body_classes(verify_email, 'saas-verify'), name = 'verify_email'
	),
	url(r'^reset/$', body_classes(reset_password, 'saas-reset'), name = 'forgot_password'),
	url(r'^reset/(?P<guid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/$',
		body_classes(reset_password, 'saas-reset', 'saas-reset-result'), name = 'reset_password'
	),
	url(r'^profile/$', body_classes(profile, 'profile'), name = 'profile'),
	url(r'^profile/edit/$', body_classes(profile_edit, 'profile', 'profile-edit'), name = 'profile_edit'),
	url(r'^login/$', body_classes(login, 'login'), name = 'login'),
	url(r'^logout/$', logout, {'next_page': '/'}, name = 'logout')
)