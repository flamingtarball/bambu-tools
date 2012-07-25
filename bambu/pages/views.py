from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from bambu.pages.models import Page
from bambu.pages.helpers import page_tree

def page(request, slug):
	page = get_object_or_404(Page, slug_hierarchical = slug)
	parts = page.slug_hierarchical.split('/')
	templates = ['pages/page.html']
	parent = 'pages/'
	
	for part in parts:
		templates.append('%s%s.html' % (parent, part))
		parent += part + '/'
	
	title_parts = [page.title or page.name]
	breadcrumb = [('', page.name)]
	backtick = '../'
	parent = page.parent
	
	while parent:
		title_parts.append(parent.title or parent.name)
		breadcrumb.append((backtick, parent.name))
		parent = parent.parent
		backtick += '../'
	
	breadcrumb.reverse()
	templates.reverse()
	
	return TemplateResponse(
		request,
		templates,
		{
			'page': page,
			'page_tree': page_tree(page, page.get_root_page(), show_root = True),
			'title_parts': title_parts,
			'breadcrumb_trail': breadcrumb,
			'menu_selection': page.get_root_page().slug_hierarchical.replace('/', '-')
		}
	)