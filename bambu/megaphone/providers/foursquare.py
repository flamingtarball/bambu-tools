from bambu.megaphone.providers import OAuthProviderBase
from django.utils import simplejson
from django.utils.timezone import utc
from dateutil.parser import parse
from datetime import datetime, timedelta
from httplib import HTTPException
import logging, re

EPOCH = datetime(1970, 1, 1).replace(tzinfo = utc)

class FoursquareProvider(OAuthProviderBase):
	verbose_name = 'Foursquare'
	server = 'foursquare.com'
	authorise_url = 'https://%s/oauth2/authenticate?client_id=%%s&redirect_uri=%%s&response_type=code' % server
	access_token_url = 'https://%s/oauth2/access_token?client_id=%%s&redirect_uri=%%s&client_secret=%%s&code=%%s&grant_type=authorization_code' % server
	identity_url = 'https://api.%s/v2/users/self?oauth_token=%%s&v=20120615' % server
	get_checkins_url = 'https://api.%s/v2/users/self/checkins?oauth_token=%%s&v=20120615' % server
	oauth_token_GET_param = 'code'
	use_ssl = False
	public = True
	token_required = False
	channels = ('checkin',)
	tags = ('checkin', 'foursquare')
	
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
		url = self.access_token_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			self.settings.get('CONSUMER_SECRET'),
			key
		)
		
		return simplejson.loads(self.open_url(url)).get('access_token')
	
	def get_identity_link(self, identity):
		return 'http://foursquare.com/user/%s' % identity
	
	def get_identity(self, access_token):
		data = self.open_url(self.identity_url % access_token)
		data = simplejson.loads(data)
		return data['response']['user']['id']
	
	def get_checkin_items(self, access_token, latest_item, **kwargs):
		from urllib import urlencode
		from os import path
		
		page = 1
		logger = logging.getLogger('bambu.megaphone')
		kwargs = {
			'limit': 250
		}
		
		url = (self.get_checkins_url % access_token) + '&'
		
		if latest_item:
			td = latest_item.date - EPOCH
			kwargs['afterTimestamp'] = int(
				(
					td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6
				) / 1e6
			)
		
		while True:
			try:
				data = self.open_url(url + urlencode(kwargs))
			except HTTPException:
				logger.error('Got bad HTTP response when looking for checkins')
				break
			except IOError:
				logger.error('IO error when looking for checkins')
				break
			
			try:
				items = simplejson.loads(data)['response'].get(
					'checkins', {}).get('items', []
				)
			except Exception, ex:
				return
			
			if len(items) == 0:
				break
			
			for item in items:
				place = item.pop('venue', None)
				if not place:
					continue
				
				primary_text = place.get('name')
				secondary_text = item.pop('shout', None)
				
				if place.get('location'):
					location = place.get('location')
					latitude, longitude = location.get('lat'), location.get('lng')
				else:
					latitude, longitude = None, None
				
				yield {
					'date': datetime.fromtimestamp(
						item.get('createdAt')
					).replace(tzinfo = utc),
					'primary_text': primary_text,
					'secondary_text': secondary_text,
					'data': item,
					'url': 'http://foursquare.com/checkins/%(id)ss' % item,
					'latitude': latitude,
					'longitude': longitude
				}
			
			if len(items) >= 250:
				kwargs['offset'] = kwargs.get('offset', 0) + len(items)
				logging.debug('Moving to offset %d' % kwargs['offset'])
			else:
				break