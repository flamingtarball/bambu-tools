from django.contrib import admin
from bambu.blog.models import *
from bambu.blog.forms import PostForm
from bambu.attachments.admin import AttachmentInline
from bambu.preview.admin import PreviewableModelAdmin

class PostAdmin(PreviewableModelAdmin):
	list_display = ('title', 'date', 'published')
	list_filter = ('published', 'categories')
	date_hierarchy = 'date'
	prepopulated_fields = {
		'slug': ('title',)
	}
	
	form = PostForm
	fieldsets = (
		(
			u'Basics',
			{
				'fields': ('title', 'date', 'published')
			}
		),
		(
			u'Post content',
			{
				'fields': ('body',)
			}
		),
		(
			u'Metadata',
			{
				'fields': ('slug', 'author', 'tags', 'categories'),
				'classes': ('collapse', 'closed')
			}
		)
	)
	
	inlines = (AttachmentInline,)
	
	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		if db_field.name == 'author':
			kwargs['initial'] = request.user
		
		return super(PostAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Post, PostAdmin)

class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)
	prepopulated_fields = {
		'slug': ('name',)
	}

admin.site.register(Category, CategoryAdmin)