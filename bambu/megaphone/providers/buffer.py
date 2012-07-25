from bambu.megaphone.providers import OAuthProviderBase
from django.utils import simplejson

class BufferProvider(OAuthProviderBase):
	verbose_name = 'Buffer'
	server = 'api.bufferapp.com'
	
	authorise_url = 'https://bufferapp.com/oauth2/authorize?client_id=%s&redirect_uri=%s&response_type=code'
	access_token_url = 'https://%s/1/oauth2/token.json?client_id=%%s&client_secret=%%s&redirect_uri=%%s&code=%%s&grant_type=authorization_code' % server
	identity_url = 'https://%s/1/profiles.json?%%s' % server
	post_message_url = 'https://%s/1/updates/create.json?%%s' % server
	use_ssl = True
	token_required = False
	oauth_token_GET_param = 'code'
	
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
		
		site = Site.objects.get_current()
		url = self.access_token_url % (
			self.settings.get('CONSUMER_KEY'),
			self.settings.get('CONSUMER_SECRET'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			key
		)
		
		return self.send_url(url, self.use_ssl)
	
	def get_identity(self, access_token):
		data = self.open_url(self.identity_url % access_token)
		data = simplejson.loads(data)
		return data['id']
	
	def parse_identity(self, data):
		data = simplejson.load(data)
		return data.get('id')
	
	def post_message(self, access_token, message, url, image = None, media = None):
		self.send_url(self.post_message_url % access_token,
			{
				'text': '%s %s' % (message, url),
				'media[link]': image,
				'media[description]': image and 'Thumbnail' or '',
			}
		)
		
		return access_token