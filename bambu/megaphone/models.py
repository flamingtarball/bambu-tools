from django.db import models
from django.utils.importlib import import_module
from django.utils.timezone import utc
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context
from django.template.defaultfilters import truncatewords
from bambu.megaphone import helpers
from bambu.megaphone.managers import *
from bambu.megaphone import site
from bambu.attachments.models import Attachment
from datetime import datetime
from taggit.managers import TaggableManager
from urllib import urlopen
from urlparse import urlparse
import logging, re

CHANNEL_NAME_EX = re.compile(r'^[\w\.]+\.get_(?P<name>\w+)_items$')

class Service(models.Model):
	user = models.ForeignKey('auth.User', related_name = 'megaphone_services')
	provider = models.CharField(max_length = 200,
		choices = helpers.get_provider_choices()
	)
	
	access_token = models.TextField()
	identity = models.CharField(max_length = 50)
	
	def __unicode__(self):
		return self.identity
	
	@property
	def shortname(self):
		shortname = self.provider[self.provider.rfind('.') + 1:]
		if shortname.endswith('Provider'):
			return shortname[:-8].lower()
		
		return shortname.lower()
	
	def get_provider_display(self):
		provider = helpers.get_provider(self.provider, True)
		return providler.verbose_name
	
	def get_identity_url(self):
		provider = helpers.get_provider(self.provider, True)
		return provider.public and provider.get_identity_link(self.identity) or ''
	
	def save(self, *args, **kwargs):
		if self.access_token and not self.identity:
			provider = helpers.get_provider(self.provider, True)
			self.identity = provider.get_identity(self.access_token)
		
		super(Service, self).save(*args, **kwargs)
	
	class Meta:
		ordering = ('identity',)
		unique_together = ('user', 'provider')

class Action(models.Model):
	service = models.ForeignKey(Service, related_name = 'actions')
	model = models.CharField(max_length = 100)
	
	message_template = models.TextField(
		default = 'New {{ noun }}: {{ title }} {{ url }}',
		help_text = 'Available variables are ' \
			'<code>verbose_name</code>, <code>verbose_name_plural</code>, ' \
			'<code>title</code> and <code>url</code>.'
	)
	
	def get_model(self):
		return models.get_model(*self.model.split('.'))
	
	def __unicode__(self):
		return unicode(
			self.get_model()._meta.verbose_name
		).capitalize()
	
	def post(self, obj, title, url, image = None, media = None):
		template = Template(self.message_template)
		model = self.get_model()
		provider = helpers.get_provider(self.service.provider, True)
		
		context = Context(
			{
				'verbose_name': model._meta.verbose_name,
				'verbose_name_plural': model._meta.verbose_name_plural,
				'noun': helpers.get_noun(model),
				'title': title,
				'url': url
			}
		)
		
		message = template.render(context)
		self.posts.post_message(self, obj, message, url, image, media)

class Post(models.Model):
	action = models.ForeignKey(Action, related_name = 'posts')
	object_id = models.PositiveIntegerField(editable = False)
	message = models.TextField()
	sent = models.DateTimeField(null = True)
	url = models.URLField(max_length = 255)
	image = models.CharField(max_length = 255)
	media = models.CharField(max_length = 255)
	objects = PostManager()
	
	def __unicode__(self):
		return truncatewords(self.message, 5)
	
	def send(self, url = None, image = None, media = None):
		provider = helpers.get_provider(self.action.service.provider, True)
		
		self.image = image or self.image
		self.media = media or self.media
		
		if provider.use_trackable_urls:
			self.url = url and provider.make_link(url) or self.url
		else:
			self.url = url or self.url
		
		access_token = provider.post_message(
			self.action.service.access_token,
			self.message, self.url, self.image, self.media
		)
		
		self.sent = datetime.utcnow().replace(tzinfo = utc)
		self.action.service.access_token = access_token
		self.action.service.save()
	
	class Meta:
		unique_together = ('action', 'object_id')

class Link(models.Model):
	url = models.URLField(max_length = 255, unique = True)
	click_count = models.PositiveIntegerField(default = 0)
	unique_click_count = models.PositiveIntegerField(default = 0)
	
	def __unicode__(self):
		return self.url
	
	@models.permalink
	def get_absolute_url(self):
		return ('megaphone_track_link', [self.pk])

class Click(models.Model):
	link = models.ForeignKey(Link, related_name = 'clicks')
	ip = models.CharField(max_length = 32)
	clicks = models.PositiveIntegerField(default = 1)
	date = models.DateTimeField(auto_now_add = True)
	
	def __unicode__(self):
		return self.ip
	
	def save(self, *args, **kwargs):
		new = not self.pk
		super(Click, self).save(*args, **kwargs)
		
		if new:
			self.link.unique_click_count += 1
		
		self.link.click_count += 1
		self.link.save()
		
	class Meta:
		unique_together = ('link', 'ip')

class Place(models.Model):
	address = models.TextField()
	latitude = models.CharField(max_length = 30)
	longitude = models.CharField(max_length = 30)
	creator = models.ForeignKey('auth.User', related_name = 'megaphone_places')
	objects = PlaceManager()
	
	def __unicode__(self):
		return self.address
	
	def save(self, *args, **kwargs):
		if self.latitude and self.longitude and not self.address:
			from django.utils import simplejson
			
			url = 'http://nominatim.openstreetmap.org/reverse?lat=%s&lon=%s&format=json' % (
				self.latitude, self.longitude
			)
			
			data = simplejson.load(
				urlopen(url)
			)
			
			self.address = data.get('display_name')
		
		super(Place, self).save(*args, **kwargs)
	
	class Meta:
		ordering = ('address',)
	
	class QuerySet(models.query.QuerySet):
		def nearby(self, latitude, longitude):
			sql = """((ACOS(SIN(%(latitude)s * PI() /
			180) * SIN(`latitude` * PI() / 180) + COS(%(latitude)s * PI() / 180) *
			COS(`latitude` * PI() / 180) * COS((%(longitude)s - 
			`longitude`) * PI() / 180)) * 180 / PI()) * 60 * 1.1515)""" % {
				'latitude': latitude,
				'longitude': longitude,
				'Model': self.model._meta.db_table
			}
			
			sql = sql.replace('\t', ' ').replace('\n', ' ')
			while '  ' in sql:
				sql = sql.replace('  ', ' ')
			
			return self.exclude(
				latitude = '',
				longitude = '',
				latitude__isnull = True,
				longitude__isnull = True
			).extra(
				select = {
					'proximity': sql
				}
			).extra(
				where = [
					'(%s) <= 25' % sql
				]
			).order_by('proximity')

class Feed(models.Model):
	user = models.ForeignKey('auth.User', related_name = 'megaphone_feeds')
	frequency = models.PositiveIntegerField(
		choices = (
			(1, u'every minute'),
			(5, u'every 5 minutes'),
			(10, u'every 10 minutes'),
			(15, u'every 15 minutes'),
			(30, u'every half an hour'),
			(60, u'every hour'),
			(180, u'every 3 hours'),
			(360, u'every 6 hours'),
			(720, u'every 12 minutes'),
			(1440, u'every day'),
			(10080, u'every week')
		)
	)
	
	checked = models.DateTimeField(null = True, editable = False)
	include = models.TextField(u'only include matching items',
		help_text = u'Put each regular expression on a new line',
		null = True, blank = True
	)
	
	exclude = models.TextField(u'exclude matching items',
		help_text = u'Put each regular expression on a new line',
		null = True, blank = True
	)
	
	content_type = models.ForeignKey(ContentType, editable = False)
	
	def __unicode__(self):
		try:
			return unicode(self.content_type.get_object_for_this_type(feed_ptr = self))
		except:
			return u''
			
	def get_include_regexes(self):
		if not hasattr(self, '_include_regexes'):
			if self.include:
				self._include_regexes = [
					re.compile(i) for i in self.include.splitlines() if i
				]
			else:
				self._include_regexes = []
			
		return self._include_regexes
	
	def get_exclude_regexes(self):
		if not hasattr(self, '_exclude_regexes'):
			if self.exclude:
				self._exclude_regexes = [
					re.compile(e) for e in self.exclude.splitlines() if e
				]
			else:
				self._exclude_regexes = []
		
		return self._exclude_regexes
	
	def include_item(self, text):
		include = True
		
		for inc in self.get_include_regexes():
			if inc.search(text) is None:
				include = False
			else:
				include = True
				continue
		
		if not include:
			return False
		
		for exc in self.get_exclude_regexes():
			if not exc.search(text) is None:
				return False
		
		return True
	
	def save(self, *args, **kwargs):
		if self.pk:
			old = type(self).objects.get(pk = self.pk)
			if old.include != self.include or old.exclude != self.exclude:
				if hasattr(self, '_include_regexes'):
					delattr(self, '_include_regexes')
				
				if hasattr(self, '_exclude_regexes'):
					delattr(self, '_exclude_regexes')
				
				logger = logging.getLogger('bambu.megaphone')
				for item in self.items.all():
					if item.primary_text and not self.include_item(item.primary_text):
						logger.debug('Deleting item %s to match new include/exclude rules' % item.url)
						item.delete()
		
		super(Feed, self).save(*args, **kwargs)
	
	def check(self):
		self.content_type.get_object_for_this_type(feed_ptr = self).check()

class ServiceFeed(Feed):
	service = models.ForeignKey(Service, related_name = 'feeds')
	channel = models.CharField(max_length = 100, choices = helpers.get_provider_channels())
	
	def __unicode__(self):
		for c, n in helpers.get_provider_channels(self.service.provider):
			if c == self.channel:
				return CHANNEL_NAME_EX.match(c).groups()[0]
		
		return ''
	
	def check(self):
		channel = helpers.check_provider_channel(
			self.service.provider, self.channel, self.service.user
		)
	
	def save(self, *args, **kwargs):
		self.content_type = ContentType.objects.get_for_model(self)
		self.user = self.service.user
		
		super(ServiceFeed, self).save(*args, **kwargs)
	
	class Meta:
		unique_together = ('service', 'channel')
		db_table = 'megaphone_feed_service'

class RSSFeed(Feed):
	url = models.URLField(u'RSS URL', unique = True)
	tags = TaggableManager()
	
	def __unicode__(self):
		scheme, netloc, path, params, query, fragment = urlparse(self.url)
		return netloc
	
	def save(self, *args, **kwargs):
		self.content_type = ContentType.objects.get_for_model(self)
		super(RSSFeed, self).save(*args, **kwargs)
	
	def check(self):
		from urllib import urlopen
		from time import mktime
		import logging, feedparser
		
		kwargs = {'page': 1}
		
		while True:
			logger = logging.getLogger('bambu.megaphone')
			
			try:
				feed = feedparser.parse(urlopen(self.url % kwargs))
			except IOError:
				logger.error('IO error when looking for feed items')
				break
			
			added = False
			
			for entry in feed.get('entries', []):
				url = helpers.fix_url(entry.link)
				if self.feed_ptr.items.filter(url = url).count() == 0:
					if self.feed_ptr.include_item(entry.title):
						logger.debug('Adding item %s' % url)
						content = entry.get('content', [])
						
						if len(content) > 0:
							content = content[0].get('value') or entry.description
						else:
							content = entry.get('description') or None
						
						try:
							Item.objects.create_item(
								feed = self.feed_ptr,
								primary_text = entry.title,
								secondary_text = content,
								url = url,
								date = datetime.fromtimestamp(
									mktime(entry.updated_parsed)
								).replace(tzinfo = utc),
								data = {},
								links = [url]
							)
							
							added = True
						except Exception, ex:
							logger.error('Error getting item: %s' % unicode(ex))
					else:
						logger.info('Ignoring item %s' % entry.link)
			
			if added:
				kwargs['page'] += 1
				logger.debug('Moving to page %(page)d' % kwargs)
			else:
				break
		
		self.feed_ptr.checked = datetime.now().replace(tzinfo = utc)
		self.feed_ptr.save()
	
	class Meta:
		db_table = 'megaphone_feed_rss'
		verbose_name = 'RSS feed'

class Item(models.Model):
	feed = models.ForeignKey(Feed, related_name = 'items')
	parent = models.ForeignKey('self', related_name = 'children', null = True, blank = True)
	date = models.DateTimeField()
	primary_text = models.TextField(null = True, blank = True)
	secondary_text = models.TextField(null = True, blank = True)
	url = models.URLField(u'URL', max_length = 255)
	thumbnail = models.ImageField(
		upload_to = helpers.upload_item_media, max_length = 255,
		null = True, blank = True
	)
	place = models.ForeignKey(Place, related_name = 'items', null = True)
	data = models.TextField()
	attachments = generic.GenericRelation(Attachment)
	tags = TaggableManager()
	objects = ItemManager()
	
	def __unicode__(self):
		return truncatewords(self.primary_text or self.url, 10)
	
	@property
	def kind(self):
		if self.feed.content_type.model == 'servicefeed':
			feed = ServiceFeed.objects.get(feed_ptr = self.feed)
			for c, n in helpers.get_provider_channels(feed.service.provider):
				if c == feed.channel:
					return CHANNEL_NAME_EX.match(c).groups()[0]
		elif self.feed.content_type.model == 'rssfeed':
			feed = RSSFeed.objects.get(feed_ptr = self.feed)
			scheme, netloc, path, params, query, fragment = urlparse(feed.url)
			return netloc.replace('.', '-')
		
		return 'item'
	
	@property
	def classes(self):
		yield '%s-item' % self.kind
		
		if self.primary_text and self.primary_text.strip():
			yield 'has-text'
		else:
			yield 'no-text'
		
		if self.secondary_text and self.secondary_text.strip():
			yield 'has-more-text'
		else:
			yield 'no-more-text'
		
		if self.thumbnail:
			yield 'has-thumbnail'
		else:
			yield 'no-thumbnail'
		
		if self.place:
			yield 'has-place'
		else:
			yield 'no-place'
		
		if self.attachments.count() > 0:
			yield 'has-attachments'
		else:
			yield 'no-attachments'
		
		if self.embeddables.count() > 0:
			yield 'has-embeddables'
		else:
			yield 'no-embeddables'
		
		if self.children.count() == 1:
			yield 'has-child'
		elif self.children.count() > 1:
			yield 'has-children'
		else:
			yield 'no-children'
		
		yield '%s-item' % self.feed.content_type.model
	
	def has_thumbnail(self):
		return not self.thumbnail is None
	
	def has_place(self):
		return not self.place is None
	
	class Meta:
		get_latest_by = 'date'
		ordering = ('-date',)
		unique_together = ('feed', 'url', 'date')

class Embeddable(models.Model):
	item = models.ForeignKey(Item, related_name = 'embeddables')
	url = models.URLField(u'URL')
	
	def __unicode__(self):
		return self.url
	
	class Meta:
		unique_together = ('url', 'item')