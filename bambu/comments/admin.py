from django.contrib import admin
from bambu.comments.models import Comment

class CommentAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'name', 'email', 'approved')
	list_filter = ('approved',)
	exclude = ('spam', 'content_type', 'object_id')
	date_hierarchy = 'sent'
	readonly_fields = ('sent',)
	
admin.site.register(Comment, CommentAdmin)