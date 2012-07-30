from bambu.megaphone.providers import OAuthProviderBase
from django.utils import simplejson
from django.utils.timezone import utc
from dateutil.parser import parse
from datetime import timedelta
from httplib import HTTPException
import logging, re

TWEET_URL_REGEX = re.compile(r'http://twitter.com/\d+/statuses/(\d+)')

class TwitterProvider(OAuthProviderBase):
	verbose_name = 'Twitter'
	server = 'api.twitter.com'
	request_token_url = 'http://%s/oauth/request_token' % server
	authorise_url = 'http://%s/oauth/authorize' % server
	access_token_url = 'http://%s/oauth/access_token' % server
	identity_url = 'http://%s/1/account/verify_credentials.json' % server
	post_message_url = 'http://%s/1/statuses/update.json' % server
	get_messages_url = 'http://%s/1/statuses/user_timeline.json' % server
	use_ssl = False
	public = True
	channels = ('tweet',)
	tags = ('message', 'twitter')
	
	def get_identity_link(self, identity):
		return 'http://twitter.com/%s' % identity
	
	def parse_identity(self, data):
		data = simplejson.load(data)
		return data.get('screen_name')
	
	def post_message(self, access_token, message, url, image = None, media = None):
		self.post_url(self.post_message_url, access_token, status = message)
		return access_token
	
	def get_tweet_items(self, access_token, latest_item, **kwargs):
		from bambu.megaphone.helpers import fix_url
		from bambu.megaphone.models import ServiceFeed
		from urllib import urlopen
		from os import path
		
		page = 1
		logger = logging.getLogger('bambu.megaphone')
		kwargs = {}
		
		if latest_item:
			matches = TWEET_URL_REGEX.match(latest_item.url)
			if not matches or len(matches.groups()) == 0:
				raise Exception('Latest tweet URL doesn\'t match expected pattern')
			
			kwargs['since_id'] = matches.groups()[0]
		
		feed = ServiceFeed.objects.get(
			service__access_token = access_token
		)
		
		while True:
			try:
				data = self.get_url(self.get_messages_url, access_token,
					count = 200, page = page, include_entities = 1, **kwargs
				)
			except HTTPException:
				logger.error('Got bad HTTP response when looking for tweets')
				break
			except IOError:
				logger.error('IO error when looking for tweets')
				break
			
			try:
				items = simplejson.load(data)
			except Exception, ex:
				return
			
			if len(items) == 0 or not isinstance(items, (list, tuple)):
				raise Exception(items)
			
			for item in items:
				user = item.pop('user')
				place = item.pop('coordinates')
				text = item.pop('text')
				attachments = []
				links = []
				
				if place:
					longitude, latitude = place.get('coordinates')
				else:
					latitude, longitude = None, None
				
				entities = item.pop('entities', {})
				existing_urls = False
				if any(entities):
					for url in entities.get('urls', []):
						fixed = fix_url(url.get('expanded_url'))
						if feed.items.filter(url__startswith = url):
							existing_urls = True
							continue
						
						text = text.replace(
							url.get('url'), fix_url(fixed)
						)
						
						links.append(fixed)
					
					if existing_urls:
						logger.debug('Ignoring item as a repost')
						continue
					
					for url in entities.get('media', []):
						url = url.get('media_url')
						attachments.append(
							{
								'file': (urlopen, url),
								'title': url[:100],
								'url': url,
								'extension': path.splitext(url)[-1]
							}
						)
				
				yield {
					'date': (
						parse(item.get('created_at'))
					).replace(tzinfo = utc),
					'primary_text': text,
					'data': item,
					'url': 'http://twitter.com/%s/statuses/%s' % (
						user.get('id'), item.get('id')
					),
					'latitude': latitude,
					'longitude': longitude,
					'attachments': attachments,
					'links': links
				}
			
			if len(items) >= 100:
				page += 1
				logger.debug('Moving to page %d' % page)
			else:
				break