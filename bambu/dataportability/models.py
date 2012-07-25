from django.db import models
from django.db.models.signals import pre_delete
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.timezone import utc
from uuid import uuid4
from datetime import datetime
from bambu.dataportability import helpers, receivers
from bambu.dataportability.managers import *
from tempfile import mkstemp
import os

class Job(models.Model):
	started = models.DateTimeField(auto_now_add = True)
	name = models.CharField(max_length = 255)
	updated = models.DateTimeField(auto_now_add = True)
	guid = models.CharField(max_length = 36, unique = True)
	handler = models.CharField(max_length = 255)
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()
	
	def __unicode__(self):
		return self.name
	
	def save(self, *args, **kwargs):
		if not self.guid:
			self.guid = unicode(uuid4())
		
		super(Job, self).save(*args, **kwargs)
	
	class Meta:
		abstract = True

class Status(models.Model):
	updated = models.DateTimeField(auto_now_add = True, auto_now = True)
	text = models.CharField(max_length = 255)
	description = models.TextField(null = True, blank = True)
	kind = models.CharField(max_length = 10,
		choices = (
			('info', u'Info'),
			('debug', u'Debug'),
			('warning', u'Warning'),
			('error', u'Error'),
			('success', u'Success')
		)
	)
	objects = StatusManager()
	
	def __unicode__(self):
		return self.text
	
	def save(self, *args, **kwargs):
		self.job.updated = datetime.utcnow().replace(tzinfo = utc)
		super(Status, self).save(*args, **kwargs)
	
	class Meta:
		abstract = True

class ImportJob(Job):
	data = models.FileField(
		storage = FileSystemStorage(location = settings.DATAPORTABILITY_IMPORT_ROOT),
		upload_to = helpers.upload_job_data
	)
	
	user = models.ForeignKey('auth.User', related_name = 'imports')
	parser = models.CharField(max_length = 255)
	
	objects = ImportJobManager()
	
	@models.permalink
	def get_absolute_url(self):
		return ('import_status', [self.guid])
	
	def start(self):
		from django.utils.importlib import import_module
		
		for job in ImportJob.objects.filter(user = self.user):
			if job.updates.count() > 0 and job.updates.order_by('-pk')[0].kind in (
				'error', 'success'
			):
				job.delete()
			elif (datetime.utcnow().replace(tzinfo = utc) - job.updated).seconds > 24 * 60 * 60:
				job.delete()
		
		def finished(status = None):
			self.updates.success('Finished import')
		
		def process(data):
			self.updates.info('Finished processing file')
			
			module, dot, klass = self.handler.rpartition('.')
			module = import_module(module)
			handler = getattr(module, klass)(self)
			
			handler.start_import(data,
				helpers.get_formats_for_parser(self.parser),
				finished
			)
		
		module, dot, klass = self.parser.rpartition('.')
		module = import_module(module)
		parser = getattr(module, klass)(self)
		parser.parse(self.data, process)
	
	class Meta:
		ordering = ('-updated',)
		get_latest_by = 'updated'
		db_table = 'dataportability_import'

class ImportStatus(Status):
	job = models.ForeignKey(ImportJob, related_name = 'updates')
	
	class Meta:
		ordering = ('updated', 'id')
		get_latest_by = 'updated'
		db_table = 'dataportability_import_status'

class ExportJob(Job):
	data = models.FileField(
		storage = FileSystemStorage(location = settings.DATAPORTABILITY_EXPORT_ROOT),
		upload_to = helpers.upload_job_data, null = True, blank = True
	)
	
	user = models.ForeignKey('auth.User', related_name = 'exports')
	writer = models.CharField(max_length = 255)
	progress = models.PositiveIntegerField(default = 0)
	
	objects = ExportJobManager()
	
	def save(self, *args, **kwargs):
		if not self.name:
			self.name = '%s_%d_%s%s' % (
				self.content_type.model,
				self.object_id,
				datetime.utcnow().replace(tzinfo = utc).strftime('%Y-%m-%d'),
				helpers.get_extension_for_writer(self.writer)
			)
		
		super(ExportJob, self).save(*args, **kwargs)
	
	@models.permalink
	def get_absolute_url(self):
		return ('export_status', [self.guid])
	
	def start(self):
		from django.utils.importlib import import_module
		
		for job in ExportJob.objects.filter(user = self.user):
			if job.progress == 100:
				job.delete()
			elif (datetime.utcnow().replace(tzinfo = utc) - job.updated).seconds > 60 * 60:
				job.delete()
		
		def finished(stream):
			stream.seek(0)
			self.data = File(stream)
			self.save()
			self.updates.success('Finished export')
		
		handle, filename = mkstemp(
			helpers.get_extension_for_writer(self.writer)
		)
		
		os.close(handle)
		stream = open(filename, 'r+w')
		
		module, dot, klass = self.handler.rpartition('.')
		module = import_module(module)
		handler = getattr(module, klass)(self)
		
		module, dot, klass = self.writer.rpartition('.')
		module = import_module(module)
		writer = getattr(module, klass)(
			stream, handler.export_wrapper,
			handler.export_item
		)
		
		handler.start_export(writer, finished)
	
	class Meta:
		ordering = ('-updated',)
		get_latest_by = 'updated'
		db_table = 'dataportability_export'

class ExportStatus(Status):
	job = models.ForeignKey(ExportJob, related_name = 'updates')
	
	class Meta:
		ordering = ('updated', 'id')
		get_latest_by = 'updated'
		db_table = 'dataportability_export_status'

pre_delete.connect(receivers.pre_import_delete, sender = ImportJob)
pre_delete.connect(receivers.pre_export_delete, sender = ExportJob)