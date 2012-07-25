from django.contrib import admin
from django import forms
from bambu.megaphone import helpers
from bambu.megaphone.models import Service, Action, ServiceFeed, RSSFeed
from bambu.megaphone.widgets import OAuthTokenInput

class ActionInline(admin.StackedInline):
	model = Action
	extra = 0
	
	def formfield_for_dbfield(self, db_field, **kwargs):
		if db_field.name == 'model':
			kwargs['widget'] = forms.Select(
				choices = helpers.get_supported_models()
			)
		
		return super(ActionInline, self).formfield_for_dbfield(db_field, **kwargs)

class ServiceFeedInline(admin.StackedInline):
	model = ServiceFeed
	extra = 0
	fields = ('service', 'channel', 'frequency', 'include', 'exclude')
	exclude = ('user',)
	
	def formfield_for_dbfield(self, db_field, **kwargs):
		if db_field.name == 'channel':
			kwargs['widget'] = forms.Select(
				choices = helpers.get_provider_channels()
			)
		
		return super(ServiceFeedInline, self).formfield_for_dbfield(db_field, **kwargs)

class ServiceAdmin(admin.ModelAdmin):
	list_display = ('identity', 'user', 'provider')
	inlines = (ActionInline, ServiceFeedInline)
	exclude = ('identity',)
	
	def formfield_for_foreignkey(self, db_field, request = None, **kwargs):
		if not request is None and db_field.name == 'user':
			kwargs['initial'] = request.user
		
		return super(ServiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
	
	def formfield_for_dbfield(self, db_field, **kwargs):
		if db_field.name == 'access_token':
			kwargs['widget'] = OAuthTokenInput(provider_field = 'provider')
			kwargs['label'] = 'Connection'
		
		return super(ServiceAdmin, self).formfield_for_dbfield(db_field, **kwargs)

admin.site.register(Service, ServiceAdmin)

class RSSFeedAdmin(admin.ModelAdmin):
	list_dislay = ('user', 'url')
	fields = ('user', 'url', 'frequency', 'include', 'exclude')

admin.site.register(RSSFeed, RSSFeedAdmin)