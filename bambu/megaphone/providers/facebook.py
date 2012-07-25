from bambu.megaphone.providers import TokenExpired, OAuthProviderBase
from django.utils import simplejson

class FacebookProvider(OAuthProviderBase):
	verbose_name = 'Facebook'
	server = 'www.facebook.com'
	authorise_url = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=%s'
	access_token_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
	renewal_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&grant_type=fb_exchange_token&fb_exchange_token=%s'
	identity_url = 'https://graph.facebook.com/me?%s'
	post_message_url = 'https://graph.facebook.com/me/links'
	permissions = ('publish_actions', 'share_item')
	token_required = False
	oauth_token_GET_param = 'code'
	use_trackable_urls = False
	
	def get_authorisation_url(self):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		return self.authorise_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			','.join(self.permissions)
		)
	
	def get_renewal_url(self, access_token):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		token = {}
		for line in access_token.split('&'):
			key, value = line.split('=')
			token[key] = value
		
		return self.renewal_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			self.settings.get('CONSUMER_SECRET'),
			token.get('access_token')
		)
	
	def swap_tokens(self, key):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		url = self.access_token_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			self.settings.get('CONSUMER_SECRET'),
			key
		)
		
		return self.open_url(url)
	
	def get_identity(self, access_token):
		data = self.open_url(self.identity_url % access_token)
		data = simplejson.loads(data)
		return data['name']
	
	def post_message(self, access_token, message, url, image = None, media = None):
		access_token = self.open_url(self.get_renewal_url(access_token))
		
		data = self.send_url(
			self.post_message_url + '?' + access_token,
			message = message,
			link = url,
			picture = image
		)
		
		try:
			data = simplejson.loads(data)
		except:
			if data:
				raise Exception(data)
		
		if 'error' in data:
			raise Exception(data['error']['message'])
		
		return access_token