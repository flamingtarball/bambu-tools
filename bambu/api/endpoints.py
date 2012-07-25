from django.contrib.auth.models import User, Group
from django.contrib.webdesign import lorem_ipsum
from django.conf.urls.defaults import patterns, url
from bambu import api
from bambu.api import helpers

class UserAPI(api.ModelAPI):
	"""
	Create, read, update and delete user accounts.
	"""
	
	fields = ('id', 'username', 'first_name', 'last_name')
	app_label_verbose = 'Users and groups'
	
	def make_random_username(self):
		return lorem_ipsum.words(1, False).lower()
	
	def make_random_first_name(self):
		return lorem_ipsum.words(1, False).capitalize()
	
	def make_random_last_name(self):
		return lorem_ipsum.words(1, False).capitalize()
	
	def get_urls(self):
		urlpatterns = super(UserAPI, self).get_urls()
		
		urlpatterns += patterns('',
			url(r'login\.(?P<format>' + '|'.join(self.allowed_formats) + ')$',
				helpers.wrap_api_function(
					self.api_site,
					self.login_view,
					1,
					('GET',)
				)
			)
		)
		
		return urlpatterns
	
	def login_view(self, request):
		return request.user

api.site.register(User, UserAPI)

class GroupAPI(api.ModelAPI):
	"""
	Create, read, update and delete user groups.
	"""
	
	fields = ('id', 'name')
	allowed_methods = ('GET',)

api.site.register(Group, GroupAPI)