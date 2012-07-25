from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.template.loader import render_to_string
from bambu.attachments import MIMETYPES, helpers
from mimetypes import guess_type
from os import path

class Attachment(models.Model):
	file = models.FileField(upload_to = helpers.upload_attachment_file)
	size = models.PositiveIntegerField(editable = False)
	mimetype = models.CharField(max_length = 50, editable = False)
	title = models.CharField(max_length = 100)
	description = models.TextField(null = True, blank = True)
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()
	
	def __unicode__(self):
		return self.title
	
	def render(self, width):
		if not self.mimetype:
			self.mimetype, encoding = guess_type(self.file.name)
		
		if not self.size:
			self.size = path.getsize(settings.MEDIA_ROOT + self.file.name)
		
		if self.mimetype in (
			'image/bmp', 'image/x-windows-bmp', 'image/gif',
			'image/jpeg', 'image/pjpeg', 'image/png'
		):
			return render_to_string(
				'attachments/image.inc.html',
				{
					'attachment': self,
					'size': '%dx9999' % width
				}
			)
		else:
			return render_to_string(
				'attachments/download.inc.html',
				{
					'attachment': self
				}
			)
	
	def clean_file(self):
		mimetype, encoding = guess_type(self.file.name)
		if not mimetype in MIMETYPES:
			raise ValidationError('Content type %s not permitted.' % mimetype)
	
	def save(self, *args, **kwargs):
		if self.file and not self.mimetype:
			self.mimetype, encoding = guess_type(self.file.name)
		
		if not self.title:
			self.title = path.splitext(self.file.name)[0]
		
		if not self.size:
			self.size = self.file.size
		
		super(Attachment, self).save(*args, **kwargs)