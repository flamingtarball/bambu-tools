from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from datetime import datetime
from bambu.activity.managers import *
from django.utils.timezone import utc

MESSAGE_PLAINTEXT = '%(user)s %(kind)s the %(content_type)s "%(object)s"%(updates)s.'
MESSAGE_HTML = '<a class="action-user-link" href="%(user_url)s">%(user)s</a> <span class="action-kind">%(kind)s</span> the <span class="content-type">%(content_type)s</span> <a href="%(object_url)s" class="action-object-url">%(object)s</a>%(updates)s.'

class Stream(models.Model):
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()
	updated = models.DateTimeField()
	objects = StreamManager()
	
	def __unicode__(self):
		return unicode(self.content_object)
	
	def get_absolute_url(self):
		try:
			return self.content_object.get_absolute_url()
		except:
			return None
	
	def save(self, *args, **kwargs):
		if not self.updated:
			self.updated = datetime.utcnow().replace(tzinfo = utc)
		
		super(Stream, self).save(*args, **kwargs)
	
	def create_action(self, user, obj, kind, message = None, updates = []):
		update_message = ''
		for i, update in enumerate(updates):
			if i == 0: # First item
				update_message += update
			elif i == len(updates) - 1: # Last item
				update_message += ' and %s' % update
			else: # Second item or greater
				update_message += ', %s' % update
		
		self.actions.create(
			user = user,
			kind = kind,
			message_plain = message,
			message_html = message,
			content_type = ContentType.objects.get_for_model(obj),
			object_id = obj.pk,
			updates = update_message
		)
	
	class QuerySet(models.query.QuerySet):
		def get_for_user(self, user):
			from bambu.activity import site
			from django.db.models import Q
			
			q = Q()
			pks = self.distinct().values_list('content_type', flat = True)
			for content_type in ContentType.objects.filter(pk__in = pks):
				model = content_type.model_class()
				test = site._registry[model](user)
				pks = model.objects.filter(**test).values_list('pk', flat = True)
				q |= Q(content_type = content_type, object_id__in = pks)
			
			return self.distinct().filter(q)

class Action(models.Model):
	stream = models.ForeignKey(Stream, related_name = 'actions')
	kind = models.CharField(max_length = 10)
	message_plain = models.CharField(max_length = 100)
	message_html = models.TextField(editable = False)
	user = models.ForeignKey('auth.User', related_name = 'actions')
	date = models.DateTimeField(auto_now_add = True)
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()
	updates = models.TextField(null = True, blank = True)
	
	def __unicode__(self):
		return self.message
	
	def _render_message(self, template):
		if hasattr(self.content_object, 'get_absolute_url'):
			url = self.content_object.get_absolute_url()
		else:
			url = '#'
		
		return template % {
			'user': self.user.get_full_name() or self.user.username,
			'user_url': '#',
			'kind': self.kind,
			'object': unicode(self.content_object),
			'object_url': url,
			'updates': self.updates and (', changing the %s' % self.updates) or '',
			'content_type': self.content_type.name
		}
	
	def save(self, *args, **kwargs):
		if not self.message_plain:
			self.message_plain = self._render_message(MESSAGE_PLAINTEXT)
		
		if not self.message_html:
			self.message_html = self._render_message(MESSAGE_HTML)
		
		super(Action, self).save(*args, **kwargs)
	
	class Meta:
		ordering = ('-date',)