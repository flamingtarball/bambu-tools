from bambu import navigation

class SAASMenuBuilder(navigation.MenuBuilder):
	def register_partials(self):
		return (
			{
				'name': 'profile',
				'description': 'Adds links to edit a user\'s profile'
			},
			{
				'name': 'legal',
				'description': 'Adds links to Terms & Conditions and Privacy pages'
			},
			{
				'name': 'saas',
				'description': 'Adds links to the Plans & Pricing page'
			}
		)
	
	def add_to_menu(self, name, items):
		if name == 'profile':
			items.append(
				{
					'url': ('profile_edit',),
					'title': u'Account',
					'title_long': u'Edit your account details',
					'selection': 'profile',
					'login': True,
					'order': 10
				}
			)
		elif name == 'legal':
			items.append(
				{
					'url': ('terms',),
					'title': u'Terms and conditions',
					'selection': 'terms'
				}
			)
			
			items.append(
				{
					'url': ('privacy',),
					'title': u'Privacy policy',
					'selection': 'privacy'
				}
			)
		else:
			items.append(
				{
					'url': ('plans',),
					'title': u'Plans and pricing',
					'selection': 'plans',
					'anon': True
				}
			)

navigation.site.register(SAASMenuBuilder)