from django.contrib import admin
from django import forms
from bambu.pages.models import Page
from bambu.attachments.admin import AttachmentInline
from bambu.preview.admin import PreviewableModelAdmin

class PageAdminForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(PageAdminForm, self).__init__(*args, **kwargs)
		
		def add_choices(queryset, indent = 0):
			if self.instance:
				queryset = queryset.exclude(pk = self.instance.pk)
			
			for page in queryset:
				choices.append((page.pk, ('-- ' * indent) + page.name))
				add_choices(page.children.all(), indent + 1)
		
		choices = [('', '---------')]
		queryset = self.fields['parent'].queryset
		add_choices(queryset.root())
		
		self.fields['parent'].widget.choices = choices
		
	class Meta:
		model = Page

class PageAdmin(PreviewableModelAdmin):
	list_display = ('link_hierarchical', 'parent', 'order_field')
	prepopulated_fields = {
		'slug': ('name',)
	}
	
	inlines = [AttachmentInline]
	form = PageAdminForm
	
	fieldsets = (
		(
			None,
			{
				'fields': ('name', 'slug', 'parent')
			},
		),
		(
			u'Page content',
			{
				'fields': ('title', 'subtitle', 'body')
			}
		),
		(
			u'Navigation',
			{
				'fields': ('order',)
			}
		)
	)
	
	def link_hierarchical(self, obj):
		spaces = 0
		parent = obj.parent
		while parent:
			spaces += 4
			parent = parent.parent
		
		return ('&nbsp;' * spaces) + obj.name
	link_hierarchical.allow_tags = True
	link_hierarchical.short_description = 'Name'
	link_hierarchical.admin_order_field = 'slug_hierarchical'
	
	def order_field(self, obj):
		return obj.order
	order_field.short_description = 'Order'
	order_field.admin_order_field = 'order_hierarchical'
	
	def save_model(self, request, obj, *args, **kwargs):
		obj.author = request.user
		obj.save()

admin.site.register(Page, PageAdmin)