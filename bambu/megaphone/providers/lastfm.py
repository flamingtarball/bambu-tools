from bambu.megaphone.providers import ProviderBase
from bambu.megaphone.helpers import unix_timestamp
from django.utils import simplejson
from django.utils.timezone import utc
from dateutil.parser import parse
from datetime import datetime, timedelta
from httplib import HTTPException
from urllib import urlopen
from os import path
import logging, re, time

EPOCH = datetime(1970, 1, 1).replace(tzinfo = utc)

class LastFMProvider(ProviderBase):
	verbose_name = 'last.fm'
	server = 'ws.audioscrobbler.com'
	authorise_url = 'http://www.last.fm/api/auth/?api_key=%s&cb=%s'
	endpoint = 'http://ws.audioscrobbler.com/2.0/'
	use_ssl = False
	public = True
	channels = ('listen',)
	token_required = True
	oauth_token_GET_param = 'token'
	albums = {}
	artists = {}
	tags = ('listen', 'lastfm')
	
	def get_token_and_auth_url(self):
		return '', self.get_authorisation_url()
	
	def get_authorisation_url(self):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		return self.authorise_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback'))
		)
	
	def sign_request(self, **kwargs):
		from hashlib import md5
		
		sig = []
		for key in sorted(kwargs.keys()):
			if key != 'format':
				sig.append('%s%s' % (key, kwargs[key]))
		
		sig.append(
			self.settings.get('CONSUMER_SECRET')
		)
		
		return md5(''.join(sig)).hexdigest()
	
	def fetch_url(self, url, **kwargs):
		from StringIO import StringIO
		from urllib import urlencode
		from copy import deepcopy
		
		connection = self.get_connection(False)
		start = 'http://%s' % self.server
		
		qsd = deepcopy(kwargs)
		qsd['api_key'] = self.settings.get('CONSUMER_KEY')
		qs = urlencode(qsd)
		if url.startswith(start):
			url = url[len(start):]
		
		start = 'https://%s' % self.server
		if url.startswith(start):
			url = url[len(start):]
		
		url = '%s?%s&api_sig=%s' % (url, qs, self.sign_request(**qsd))
		connection.request('GET', url)
		return connection.getresponse()
	
	def verify_and_swap(self, request):
		return self.swap_tokens(
			request.GET.get(self.oauth_token_GET_param)
		)
	
	def swap_tokens(self, key):
		return simplejson.load(
			self.fetch_url(self.endpoint,
				token = key,
				method = 'auth.getSession',
				format = 'json'
			)
		).get('session', {}).get('key')
	
	def get_identity(self, access_token):
		json = simplejson.load(
			self.fetch_url(self.endpoint,
				sk = access_token,
				method = 'user.getInfo',
				format = 'json'
			)
		)
		
		return json.get('user', {}).get('name')
	
	def get_artist(self, mbid, logger):
		if not mbid in self.artists:
			logger.debug('Getting artist info for "%s"' % mbid)
			data = simplejson.load(
				self.fetch_url(self.endpoint,
					method = 'artist.getInfo',
					mbid = mbid,
					format = 'json'
				)
			)
			
			self.artists[mbid] = data.get('artist')
		
		return self.artists[mbid]
	
	def get_album(self, mbid, logger):
		if not mbid in self.albums:
			logger.debug('Getting album info for "%s"' % mbid)
			data = simplejson.load(
				self.fetch_url(self.endpoint,
					method = 'album.getInfo',
					mbid = mbid,
					format = 'json'
				)
			)
			
			self.albums[mbid] = data.get('album')
		
		return self.albums[mbid]
	
	def get_listen_items(self, access_token, latest_item, identity, **kwargs):
		logger = logging.getLogger('bambu.megaphone')
		kwargs = {'page': 1}
		
		if not latest_item is None:
			kwargs['from'] = unix_timestamp(latest_item.date)
			kwargs['to'] = unix_timestamp(datetime.now().replace(tzinfo = utc))
		
		while True:
			try:
				data = self.fetch_url(self.endpoint,
					sk = access_token,
					method = 'user.getRecentTracks',
					limit = 200,
					format = 'json',
					user = identity,
					**kwargs
				)
			except HTTPException:
				logger.error('Got bad HTTP response when looking for latest tracks')
				break
			except IOError:
				logger.error('IO error when looking for latest tracks')
				break
			
			try:
				data = simplejson.load(data)
				
				if 'error' in data and 'message' in data:
					logger.error(data.get('message'))
					break
			except:
				logger.error('Parsing error')
				break
			
			tracks = data.get('recenttracks', {}).get('track', [])
			if not any(tracks):
				break
			
			if isinstance(tracks, dict):
				tracks = [tracks]
			
			added = False
			for track in tracks:
				album = track.pop('album', {})
				artist = track.pop('artist', {})
				text = '%s - %s' % (
					artist.pop('#text', '(Unknown)'),
					track.pop('name', '(Unknown)')
				)
				
				if(text == '(Unknown) - (Unknown)'):
					continue
				
				attachments = []
				parent = None
				
				if not track.get('date'):
					continue
				
				date = parse(track.pop('date', {}).get('#text')).replace(tzinfo = utc)
				if latest_item and date < latest_item.date:
					continue
				
				if 'mbid' in album and album['mbid']:
					try:
						album = self.get_album(album['mbid'], logger)
					except:
						logger.error('Unable to get info for album "%s"' % album['mbid'])
						continue
					
					parent = {
						'primary_text': album.get('name'),
						'secondary_text': album.get('artist'),
						'url': album.get('url'),
						'date': date,
						'data': album,
						'attachments': []
					}
					
					for image in album.get('image', []):
						if image.get('size') == 'large':
							url = image.get('#text')
							
							parent['attachments'].append(
								{
									'file': (urlopen, url),
									'title': album.get('name'),
									'url': url,
									'extension': path.splitext(url)[-1]
								}
							)
				
				yield {
					'primary_text': text,
					'url': track.pop('url'),
					'date': date,
					'data': track,
					'parent': parent
				}
				
				added = True
			
			if added:
				kwargs['page'] += 1
				logger.debug('Moving to page %(page)d' % kwargs)
				# sleep(1)
			else:
				logger.debug('No new items added; abandoning pagination')
				break