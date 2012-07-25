from bambu.pages.models import Page

def page_tree(selected = None, parent = None, show_root = False):
	items = []
	
	if parent and show_root and parent.children.count() > 0:
		if selected and parent.pk == selected.pk:
			is_selected = ' class="active"'
		else:
			is_selected = ''
		
		items.append(
			'<li%s><a href="%s">%s</a>%s</li>' % (
				is_selected,
				parent.get_absolute_url(),
				parent.name,
				page_tree(selected, parent)
			)
		)
	else:
		for page in Page.objects.filter(parent = parent):
			if selected and page.pk == selected.pk:
				is_selected = ' class="active"'
			else:
				is_selected = ''
		
			items.append(
				'<li%s><a href="%s">%s</a>%s</li>' % (
					is_selected,
					page.get_absolute_url(),
					page.name,
					page_tree(selected, page)
				)
			)
	
	if len(items) > 0:
		return '<ol class="page-navigation">%s</ol>' % ''.join(items)
	else:
		return ''