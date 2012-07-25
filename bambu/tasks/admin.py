from django.contrib import admin
from bambu.tasks.models import Task

class TaskAdmin(admin.ModelAdmin):
	list_display = ('function', 'updated', 'state')
	list_filter = ('state',)
	date_hierarchy = 'updated'
	readonly_fields = ('function', 'state', 'created', 'updated')
	
admin.site.register(Task, TaskAdmin)