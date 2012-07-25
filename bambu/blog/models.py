from django.db import models
from django.contrib.contenttypes import generic
from django.utils.timezone import utc
from taggit.managers import TaggableManager
from bambu.blog.managers import *
from bambu.blog import helpers
from bambu.comments.models import Comment
from bambu.attachments.models import Attachment
from bambu.preview.models import Preview
from bambu import megaphone
from datetime import datetime

class Category(models.Model):
	name = models.CharField(max_length = 100)
	slug = models.SlugField(max_length = 100)
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('name',)
		verbose_name_plural = 'categories'

class Post(models.Model):
	author = models.ForeignKey('auth.User', related_name = 'blog_posts')
	title = models.CharField(max_length = 100)
	slug = models.SlugField(max_length = 100)
	date = models.DateTimeField()
	published = models.BooleanField(default = True)
	broadcast = models.BooleanField(editable = False)
	body = models.TextField()
	tags = TaggableManager()
	categories = models.ManyToManyField(Category, related_name = 'posts',
		null = True, blank = True
	)
	attachments = generic.GenericRelation(Attachment)
	comments = generic.GenericRelation(Comment)
	objects = PostManager()
	
	@models.permalink
	def get_absolute_url(self):
		return (
			'blog_post', (
				str(self.date.year).zfill(4),
				str(self.date.month).zfill(2),
				str(self.date.day).zfill(2),
				self.slug
			)
		)
	
	def __unicode__(self):
		return self.title
	
	def save(self, *args, **kwargs):
		publish = False
		if self.pk:
			old = Post.objects.get(pk = self.pk)
			if self.published and not old.published:
				publish = True
		elif self.published:
			publish = True
		
		super(Post, self).save(*args, **kwargs)
		Preview.objects.clear_for_model(self, self.author)
		
		if publish and self.date <= datetime.utcnow().replace(tzinfo = utc):
			self.publish()
	
	def publish(self):
		megaphone.broadcast(self, self.author)
		self.broadcast = True
	
	class Meta:
		ordering = ('-date',)
		get_latest_by = 'date'
	
	class QuerySet(models.query.QuerySet):
		def live(self):
			return self.filter(
				date__lte = datetime.utcnow().replace(tzinfo = utc),
				published = True
			)

megaphone.site.register(Post, unicode, helpers.get_post_image,
	verb = 'publish a blog post',
	noun = 'blog post', staff_only = True
)