from django.db.models import Manager
from django.core.files import File
from django.utils import simplejson
from django.conf import settings
from bambu.oembed import URL_PATTERNS
from mimetypes import guess_type
import logging, tempfile, os, re

OEMBED_PATTERNS = list(URL_PATTERNS) + getattr(settings, 'OEMBED_URL_PATTERNS', [])
OEMBED_WIDTH = getattr(settings, 'OEMBED_WIDTH', 640)

class PostManager(Manager):
	def post_message(self, action, obj, message, url, image = None, media = None):
		post = self.model(
			action = action,
			object_id = obj.pk,
			message = message
		)
		
		post.send(url, image, media)
		post.save()

class PlaceManager(Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)

	def nearby(self, latitude, longitude):
		return self.get_query_set().nearby(latitude, longitude)
		
class ItemManager(Manager):
	def create_item(self, feed, url, data, attachments = [], links = [], parent = None, **kwargs):
		from bambu.megaphone.models import Place
		
		logger = logging.getLogger('bambu.megaphone')
		
		if not parent is None:
			try:
				kwargs['parent'] = self.get(
					feed = feed,
					url__iexact = parent['url'],
					date__day = parent['date'].day,
					date__month = parent['date'].month,
					date__year = parent['date'].year
				)
			except self.model.DoesNotExist:
				logging.debug('Adding parent %(url)s' % parent)
				kwargs['parent'] = self.create_item(
					feed = feed,
					**parent
				)
		
		latitude, longitude = kwargs.pop('latitude', None), kwargs.pop('longitude', None)
		
		if latitude and longitude:
			try:
				place, pc = Place.objects.get_or_create(
					latitude = unicode(latitude)[:6],
					longitude = unicode(longitude)[:6],
					creator = feed.user
				)
			except:
				place = None
				logger.error(
					'Unable to reverse-geocode location %s, %s' % (latitude, longitude)
				)
			
			if pc:
				logger.debug('Geocoded address %s' % place.address)
		else:
			place = None
		
		images = {}
		for a in attachments:
			mimetype, encoding = guess_type(a['url'])
			if mimetype and (mimetype.startswith('image/') or mimetype.startswith('x-image/')):
				handle, filename = tempfile.mkstemp(
					a['extension']
				)
				
				if isinstance(a['file'], tuple):
					func, name = a['file']
					
					try:
						f = func(name)
					except:
						logger.error('Error when downloading attachment')
						return
				else:
					f = a['file']
				
				os.write(handle, f.read())
				os.close(handle)
				
				kwargs['thumbnail'] = File(
					open(filename, 'r')
				)
				
				images[a['url']] = filename
				break
		
		if isinstance(data, (list, tuple, dict)):
			data = simplejson.dumps(data)
		
		item = feed.items.create(
			place = place,
			url = url,
			data = data,
			**kwargs
		)
		
		for a in attachments:
			if not a['url'] in images:
				handle, filename = tempfile.mkstemp(
					a['extension']
				)
				
				if isinstance(a['file'], tuple):
					func, name = a['file']
					
					try:
						f = func(name)
					except:
						logger.error('Error when downloading attachment')
						return
				else:
					f = a['file']
				
				os.write(handle, f.read())
				os.close(handle)
			else:
				filename = images[a['url']]
			
			item.attachments.create(
				file = File(
					open(filename, 'r')
				)
			)
			
			os.remove(filename)
		
		for l in links:
			for (pattern, endpoint, format) in OEMBED_PATTERNS:
				if not re.match(pattern, l, re.IGNORECASE) is None:
					if item.embeddables.filter(url__iexact = l).count() == 0:
						item.embeddables.create(url = l)
						logger.debug('Found embeddable resource %s' % l)
					
					break
		
		return item