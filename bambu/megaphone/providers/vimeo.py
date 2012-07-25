from bambu.megaphone.providers import OAuthProviderBase
from oauth.oauth import OAuthToken, OAuthRequest
from django.utils import simplejson
from django.utils.timezone import utc
from dateutil.parser import parse
from datetime import timedelta
from httplib import HTTPException
from StringIO import StringIO
import logging, re

TWEET_URL_REGEX = re.compile(r'http://vimeo.com/\d+/statuses/(\d+)')

class VimeoProvider(OAuthProviderBase):
	verbose_name = 'Vimeo'
	server = 'vimeo.com'
	request_token_url = 'http://%s/oauth/request_token' % server
	authorise_url = 'http://%s/oauth/authorize' % server
	access_token_url = 'http://%s/oauth/access_token' % server
	endpoint = 'http://%s/api/rest/v2?format=json&method=%%s' % server
	get_videos_url = endpoint % ''
	use_ssl = False
	public = True
	channels = ('video',)
	
	def get_identity_link(self, identity):
		return 'http://vimeo.com/%s' % identity
	
	def get_identity(self, access_token):
		return self.parse_identity(
			self.fetch_url(self.endpoint, access_token,
				method = 'vimeo.people.getInfo',
				format = 'json'
			)
		)
	
	def parse_identity(self, data):
		data = simplejson.load(data)
		return data.get('person', {}).get('username')
	
	def get_video_items(self, access_token, latest_item, **kwargs):
		logger = logging.getLogger('bambu.megaphone')
		page = 1
		
		while True:
			try:
				data = self.fetch_url(self.endpoint, access_token,
					method = 'vimeo.videos.getUploaded',
					format = 'json',
					page = page
				)
			except HTTPException:
				logger.error('Got bad HTTP response when looking for videos')
				break
			except IOError:
				logger.error('IO error when looking for videos')
				break
			
			try:
				data = simplejson.load(data)
			except Exception, ex:
				return
			
			items = data.get('videos', {}).get('video', [])
			perpage = data.get('videos', {}).get('perpage', len(items))
			
			if len(items) == 0:
				break
			
			for item in items:
				if item.get('embed_privacy') != 'anywhere':
					continue
				
				yield {
					'date': (
						parse(item.get('upload_date'))
					).replace(tzinfo = utc),
					'primary_text': item.pop('title'),
					'data': item,
					'url': 'http://vimeo.com/%(id)s' % item,
					'links': ['http://vimeo.com/%(id)s' % item]
				}
			
			if len(items) == perpage:
				page += 1
				logger.debug('Moving to page %d' % page)
			else:
				break