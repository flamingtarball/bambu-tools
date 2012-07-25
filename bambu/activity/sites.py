from django.db.models import ForeignKey, ManyToManyField, get_model
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.core.exceptions import ImproperlyConfigured
from bambu.activity import receivers
import logging

class AlreadyRegistered(Exception):
	pass

class NotRegistered(Exception):
	pass

class ActivitySite(object):
	_registry = {}
	_models = {}
	
	def __init__(self):
		self.logger = logging.getLogger('bambu.activity')
	
	def register_stream(self, model, user_test):
		if model._meta.abstract:
			raise ImproperlyConfigured(
				'The model %s is abstract, so it cannot be registered with Megaphone.' % (
					model.__name__
				)
			)
		
		if model in self._registry:
			raise AlreadyRegistered('Model %s already registered.' % model)
		
		self._registry[model] = user_test
		self.logger.debug('Registered stream model %s' % model._meta.verbose_name.capitalize())
		post_save.connect(receivers.post_save, sender = model)
	
	def register_poster(self, model, stream_field, *actions):
		field = getattr(model, stream_field).field
		stream = field.rel.to
		
		if isinstance(stream, str):
			stream = get_model(*stream.split('.'))
		
		if not stream in self._registry:
			raise NotRegistered('Model %s not registered.' % stream)
		
		self._models[model] = stream_field
		
		if isinstance(field, ForeignKey):
			self.logger.debug(
				'Registered poster model %s for stream model %s' % (
					model._meta.verbose_name.capitalize(),
					stream._meta.verbose_name.capitalize()
				)
			)
		elif isinstance(field, ManyToManyField):
			m2m_changed.connect(receivers.m2m_changed)
			
			self.logger.debug(
				'Registered poster model %s for many-to-many stream model %s' % (
					model._meta.verbose_name.capitalize(),
					stream._meta.verbose_name.capitalize()
				)
			)
		else:
			raise ImproperlyConfigured('Connecting field must be a ForeignKey or ManyToMany field')
		
		pre_save.connect(receivers.pre_save, sender = model)
		pre_delete.connect(receivers.pre_delete, sender = model)
		post_save.connect(receivers.post_save, sender = model)