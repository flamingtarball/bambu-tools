from bambu import navigation

class SAASMenuBuilder(navigation.MenuBuilder):
	def register_partials(self):
		return (
			{
				'name': 'api',
				'description': 'Adds a link to the API documentation'
			},
		)
	
	def add_to_menu(self, name, items):
		items.append(
			{
				'url': ('api:doc',),
				'title': u'Developers',
				'selection': 'terms'
			}
		)

navigation.site.register(SAASMenuBuilder)