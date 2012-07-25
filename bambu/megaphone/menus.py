from bambu import navigation

class MegaphoneMenuBuilder(navigation.MenuBuilder):
	def register_partials(self):
		return (
			{
				'name': 'profile',
				'description': 'Adds links to edit a user\'s profile'
			},
		)
	
	def add_to_menu(self, name, items):
		items.append(
			{
				'url': ('profile_connect',),
				'title': u'Connect your social profiles',
				'selection': 'profile',
				'login': True
			}
		)

navigation.site.register(MegaphoneMenuBuilder)