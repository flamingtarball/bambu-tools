from bambu.api.options import *
from bambu.api.sites import APISite

site = APISite()

def autodiscover():
	from django.conf import settings
	from django.utils.importlib import import_module
	from django.utils.module_loading import module_has_submodule
	from copy import copy, deepcopy
	from bambu.api.endpoints import *
	
	for app in settings.INSTALLED_APPS:
		mod = import_module(app)
		
		try:
			before_import_registry = copy(site._registry)
			import_module('%s.api' % app)
		except:
			site._registry = before_import_registry
			if module_has_submodule(mod, 'api'):
				raise