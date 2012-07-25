from django.db import models
from django.utils import simplejson
from django.utils.importlib import import_module
from django.utils.timezone import utc
from django.conf import settings
from bambu.tasks import TASK_QUEUED, TASK_PROCESSING, TASK_COMPLETE, TASK_FAILED, \
	TASK_CANCELLED, TASK_LIFESPAN
from bambu.tasks.managers import *
from bambu.tasks.threads import TaskThread
from datetime import datetime, timedelta
import sys, logging

LIFESPAN = getattr(settings, 'TASK_LIFESPAN', TASK_LIFESPAN)

class Task(models.Model):
	function = models.TextField()
	scheduled_for = models.DateTimeField(null = True, blank = True)
	arguments = models.TextField(null = True, blank = True, editable = False)
	keyword_arguments = models.TextField(null = True, blank = True, editable = False)
	state = models.IntegerField(
		choices = (
			(TASK_QUEUED, u'Queued'),
			(TASK_PROCESSING, u'Processing'),
			(TASK_COMPLETE, u'Complete'),
			(TASK_FAILED, u'Failed'),
			(TASK_CANCELLED, u'Cancelled')
		),
		default = TASK_QUEUED
	)
	
	created = models.DateTimeField(auto_now_add = True)
	updated = models.DateTimeField(null = True, blank = True)
	
	success_callback_function = models.TextField(null = True, blank = True)
	success_callback_arguments = models.TextField(null = True, blank = True, editable = False)
	success_callback_keyword_arguments = models.TextField(null = True, blank = True, editable = False)
	
	failure_callback_function = models.TextField(null = True, blank = True)
	failure_callback_arguments = models.TextField(null = True, blank = True, editable = False)
	failure_callback_keyword_arguments = models.TextField(null = True, blank = True, editable = False)
	
	objects = TaskManager()
	
	def __unicode__(self):
		args = []
		kwargs = {}
		
		if self.arguments:
			args = simplejson.loads(self.arguments)
		
		if self.keyword_arguments:
			kwargs = simplejson.loads(self.keyword_arguments)
			kwargs = ', '.join(
				[
					'%s = %s' % (
						key, value
					) for (key, value) in kwargs.items()
				]
			)
		else:
			kwargs = ''
		
		if any(args):
			args = ', '.join(args)
			if kwargs:
				args += ', ' + kwargs
		else:
			args = kwargs
		
		return '%s(%s)' % (self.function, args)
	
	def start(self):
		if '.' in self.function:
			split = self.function.split('.')
			modname = '.'.join(split[:-1])
			funcname = split[-1]
			
			try:
				mod = import_module(modname)
				function = getattr(mod, '%s' % funcname)
			except:
				self.delete()
				raise
		else:
			self.delete()
			raise Exception('Function must be contained within a module.')
		
		args = []
		kwargs = {}
		
		if self.arguments:
			args = simplejson.loads(self.arguments)
		
		if self.keyword_arguments:
			kwargs = simplejson.loads(self.keyword_arguments)
		
		TaskThread(
			self.pk,
			function,
			args,
			kwargs
		).start()
		
		Task.objects.filter(
			updated__lte = datetime.utcnow().replace(tzinfo = utc) - timedelta(days = LIFESPAN)
		).delete()
	
	def callback(self, success = True, value = None):
		if success:
			function = self.success_callback_function
			arguments = self.success_callback_arguments
			keyword_arguments = self.success_callback_keyword_arguments
		else:
			function = self.failure_callback_function
			arguments = self.failure_callback_arguments
			keyword_arguments = self.failure_callback_keyword_arguments
		
		if not function:
			return
		
		if '.' in function:
			split = function.split('.')
			modname = '.'.join(split[:-1])
			funcname = split[-1]
			
			try:
				mod = import_module(modname)
				function = getattr(mod, '%s' % funcname)
			except:
				raise
		else:
			raise Exception('Function must be contained within a module.')
		
		args = []
		kwargs = {}
		
		if arguments:
			args = simplejson.loads(arguments)
		
		if keyword_arguments:
			kwargs = simplejson.loads(keyword_arguments)
		
		logger = logging.getLogger('bambu.tasks')
		
		try:
			function(value, *args, **kwargs)
		except Exception, ex:
			logger.error(
				'Error running %s callback' % (success and 'success' or 'failure'),
				extra = {
					'data': {
						'args': arguments,
						'kwargs': keyword_arguments,
						'error': unicode(ex)
					}
				}
			)
	
	class Meta:
		ordering = ('created',)
		get_latest_by = 'updated'
		
	class QuerySet(models.query.QuerySet):
		pass