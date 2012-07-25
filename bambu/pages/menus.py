from bambu import navigation
from bambu.pages.models import Page

class PageMenuBuilder(navigation.MenuBuilder):
	def register_partials(self):
		return (
			{
				'name': 'pages',
				'description': 'Lists all the root-level pages in the site'
			},
		)
	
	def add_to_menu(self, name, items):
		for page in Page.objects.root():
			items.append(
				{
					'url': ('page', [page.slug_hierarchical]),
					'title': page.name,
					'selection': page.get_root_page().slug_hierarchical.replace('/', '-'),
					'order': 10 + page.order
				}
			)

navigation.site.register(PageMenuBuilder)