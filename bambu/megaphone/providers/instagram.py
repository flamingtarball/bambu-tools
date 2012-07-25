from bambu.megaphone.providers import OAuthProviderBase
from django.utils import simplejson
from django.utils.timezone import utc
from dateutil.parser import parse
from datetime import datetime, timedelta
from httplib import HTTPException
import logging, re

EPOCH = datetime(1970, 1, 1).replace(tzinfo = utc)

class InstagramProvider(OAuthProviderBase):
	verbose_name = 'Instagram'
	server = 'api.instagram.com'
	authorise_url = 'https://%s/oauth/authorize?client_id=%%s&redirect_uri=%%s&response_type=code' % server
	access_token_url = 'https://%s/oauth/access_token' % server
	identity_url = 'https://%s/v1/users/self/?access_token=%%s' % server
	get_photos_url = 'https://%s/v1/users/self/media/recent/?access_token=%%s' % server
	oauth_token_GET_param = 'code'
	use_ssl = True
	public = True
	token_required = False
	channels = ('photo',)
	
	def get_authorisation_url(self):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		return self.authorise_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback'))
		)
	
	def swap_tokens(self, key):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		from django.utils import simplejson
		
		site = Site.objects.get_current()
		data = simplejson.loads(
			self.send_url(self.access_token_url,
				client_id = self.settings.get('CONSUMER_KEY'),
				redirect_uri = 'http://%s%s' % (site.domain, reverse('megaphone_callback')),
				client_secret = self.settings.get('CONSUMER_SECRET'),
				code = key,
				grant_type = 'authorization_code'
			)
		)
		
		if not 'access_token' in data:
			raise Exception(data)
		
		return data.get('access_token')
	
	def get_identity_link(self, identity):
		return 'http://instagram.com/user/%s' % identity
	
	def get_identity(self, access_token):
		data = self.open_url(self.identity_url % access_token)
		data = simplejson.loads(data)
		return data['data']['username']
	
	def get_photo_items(self, access_token, latest_item, **kwargs):
		from urllib import urlopen, urlencode
		from os import path
		
		page = 1
		logger = logging.getLogger('bambu.megaphone')
		kwargs = {
			'count': 100
		}
		
		url = (self.get_photos_url % access_token) + '&' + urlencode(kwargs)
		
		while True:
			try:
				data = self.open_url(url)
			except HTTPException:
				logger.error('Got bad HTTP response when looking for photos')
			except IOError:
				logger.error('IO error when looking for photos')
				break
			
			try:
				data = simplejson.loads(data)
			except Exception, ex:
				return
			
			items = data.get('data', [])
			if len(items) == 0:
				break
			
			for item in items:
				if item.get('type') != 'image':
					continue
				
				place = item.pop('location', None)
				text = (item.get('caption') or {}).get('text') or None
				user = item.pop('user')
				attachments = []
				
				images = item.pop('images', {})
				standard_resolution = images.get('standard_resolution', {})
				
				if standard_resolution.get('url'):
					url = standard_resolution.get('url')
					attachments.append(
						{
							'file': (urlopen, url),
							'title': url[:100],
							'url': url,
							'extension': path.splitext(url)[-1]
						}
					)
				
				if place:
					latitude, longitude = place.get('latitude'), place.get('longitude')
				else:
					latitude, longitude = None, None
				
				yield {
					'date': datetime.fromtimestamp(
						int(item.get('created_time'))
					).replace(tzinfo = utc),
					'primary_text': text,
					'data': item,
					'url': item.get('link'),
					'latitude': latitude,
					'longitude': longitude,
					'attachments': attachments
				}
			
			pagination = data.get('pagination')
			if pagination:
				logger.debug('Moving to next page')
				url = pagination.get('next_url')
			else:
				break
			
			if not url:
				break