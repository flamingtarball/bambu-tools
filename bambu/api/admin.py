from django.contrib import admin
from bambu.api.models import App

class AppAdmin(admin.ModelAdmin):
	list_display = ('name', 'admin', 'deployment')

admin.site.register(App, AppAdmin)