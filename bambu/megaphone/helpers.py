from django.conf import settings
from django.utils.importlib import import_module
from django.utils.timezone import utc
from django.utils import simplejson
from urllib import urlopen
from datetime import datetime
from uuid import uuid4
from os import path

def get_provider(name, instance = False):
	mod, dot, klass = name.rpartition('.')
	mod = import_module(mod)
	klass = getattr(mod, klass)
	
	if instance:
		for (cname, details) in settings.MEGAPHONE_PROVIDERS:
			if cname == name:
				return klass(**details)
		
		return klass()
	else:
		return klass

def get_provider_choices(can_post = False):
	providers = []
	
	for (name, details) in settings.MEGAPHONE_PROVIDERS:
		klass = get_provider(name)
		if can_post:
			t = (name, klass.verbose_name, klass.can_post)
		else:
			t = (name, klass.verbose_name)
		
		providers.append(t)
	
	return tuple(providers)

def get_identity_link(provider, identity):
	provider = get_provider(provider, True)
	return provider.get_identity_link(identity)

def get_provider_channels(provider = None):
	if provider and not isinstance(provider, (list, tuple)):
		providers = [provider]
	else:
		providers = [p[0] for p in get_provider_choices()]
	
	channels = []
	for provider in providers:
		klass = get_provider(provider, True)
		channels.extend(klass.get_channels())
	
	return channels

def check_provider_channel(provider, channel, user):
	from bambu.megaphone.models import ServiceFeed, Item, Place
	import logging, socket
	
	feed = ServiceFeed.objects.get(
		service__provider = provider,
		service__user = user,
		channel = channel
	)
	
	try:
		latest = feed.items.latest()
	except Item.DoesNotExist:
		latest = None
	
	logger = logging.getLogger('bambu.megaphone')
	provider = get_provider(provider, True)
	socket.setdefaulttimeout(5)
	
	for c, n in provider.get_channels():
		if c == channel:
			func = getattr(provider, c[c.rfind('.') + 1:])
			for i in func(feed.service.access_token, latest, identity = feed.service.identity):
				if feed.items.filter(url = i['url']).count() == 0:
					if feed.include_item(i['primary_text']):
						logger.debug('Adding item %s' % i['url'])
						
						try:
							Item.objects.create_item(
								feed = feed,
								**i
							)
						except Exception, ex:
							raise
							logger.error('Error getting item: %s' % unicode(ex))
					else:
						logging.info('Ignoring item %s' % i['url'])
			
			feed.checked = datetime.utcnow().replace(tzinfo = utc)
			feed.save()
			return

def make_verb(model):
	prefix = 'a'
	if model._meta.app_label[0] in ('a', 'e', 'i', 'o'):
		prefix += 'n'
	
	return 'create %s %s %s' % (
		prefix,
		model._meta.app_label.replace('_', ' '),
		unicode(model._meta.verbose_name)
	)

def get_supported_models():
	models = []
	from bambu.megaphone import site
	
	for (klass, details) in site._registry.items():
		models.append(
			(
				'%s.%s' % (klass._meta.app_label, klass._meta.module_name),
				'%s (%s)' % (
					unicode(klass._meta.verbose_name).capitalize(),
					klass._meta.app_label
				)
			)
		)
	
	return tuple(models)

def fix_media_url(url):
	if not url.startswith('http://') and not url.startswith('https://'):
		if url.startswith('/'):
			url = url[1:]
		
		url = settings.MEDIA_URL + url
	else:
		url = url
	
	q = url.find('?')
	if q > -1:
		url = url[:q]
	
	return url

def get_noun(model):
	from bambu.megaphone import site
	
	return site._registry.get(
		model, {}
	).get(
		'noun', unicode(model._meta.verbose_name)
	)
	
def upload_item_media(instance, filename):
	return 'megaphone/%s/%s%s' % (
		instance.feed.service.user,
		unicode(uuid4()),
		path.splitext(filename)[-1]
	)
	
def fix_url(url):
	try:
		response = urlopen(url)
		code = response.getcode()
	
		if code >= 200 and code < 400:
			return response.url
		else:
			return url
	except:
		return url