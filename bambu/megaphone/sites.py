from bambu.megaphone import helpers
import logging

class AlreadyRegistered(Exception):
	pass

class NotRegistered(Exception):
	pass

class MegaphoneSite(object):
	_registry = {}
	
	def register(self, model, title_field = unicode, image_field = None, media_field = None, **kwargs):
		if model._meta.abstract:
			raise ImproperlyConfigured(
				'The model %s is abstract, so it cannot be registered with Megaphone.' % (
					model.__name__
				)
			)
		
		if not hasattr(model, 'get_absolute_url'):
			raise ImproperlyConfigured(
				'The model %s has no get_absolute_url function.' % (
					model.__name__
				)
			)
		
		if model in self._registry:
			raise AlreadyRegistered('Model %s already registered.' % model)
		
		self._registry[model] = {
			'title_field': title_field,
			'image_field': image_field,
			'media_field': media_field,
			'verb': kwargs.get('verb', helpers.make_verb(model)),
			'noun': kwargs.get('noun', unicode(model._meta.verbose_name)),
			'staff_only': kwargs.get('staff_only', False)
		}