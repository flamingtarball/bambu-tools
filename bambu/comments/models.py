from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from bambu.comments.managers import *
from bambu.mail.shortcuts import render_to_mail

class Comment(models.Model):
	name = models.CharField(max_length = 50)
	website = models.URLField(max_length = 255, null = True, blank = True)
	email = models.EmailField(max_length = 255)
	sent = models.DateTimeField(auto_now_add = True)
	approved = models.BooleanField()
	spam = models.BooleanField()
	body = models.TextField()
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()
	objects = CommentManager()
	
	def __unicode__(self):
		return u'Re: %s' % unicode(self.content_object)
	
	def save(self, *args, **kwargs):
		if self.spam:
			self.approved = False
		
		new = not self.pk
		if new:
			self.approved = Comment.objects.filter(
				email__iexact = self.email,
				approved = True,
				spam = False
			).count() > 0
		
		super(Comment, self).save(*args, **kwargs)
		
		if new:
			render_to_mail(
				u'New comment submitted',
				'comments/mail.txt',
				{
					'comment': self,
					'author': self.content_object.author
				},
				self.content_object.author
			)
	
	class Meta:
		ordering = ('-sent',)
		get_latest_by = 'sent'
		
	class QuerySet(models.query.QuerySet):
		def live(self):
			return self.filter(
				approved = True,
				spam = False
			)