from django.http import HttpResponse
from django.conf.urls.defaults import patterns
from django.forms.models import modelform_factory
from django.db.models import get_model

class AuthenticationBase(object):
	verbose_name = 'Authentication'
	app_model = None
	
	def authenticate(self, request):
		raise NotImplementedError('Method not implemented.')
	
	def challenge(self, request):
		return HttpResponse('Answer: friend or foe?')
	
	def get_urls(self):
		return patterns('')
	
	def get_editor_form(self):
		if self.app_model:
			return modelform_factory(
				get_model(*self.app_model.split('.')),
				exclude = ('admin', 'http_login', 'http_signup')
			)

class AnonymousAuthentication(AuthenticationBase):
	verbose_name = 'Anonymous access'

	def authenticate(self, request):
		return True