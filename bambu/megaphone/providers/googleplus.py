from bambu.megaphone.providers import OAuthProviderBase
from django.utils import simplejson

class GooglePlusProvider(OAuthProviderBase):
	verbose_name = 'Google+'
	server = 'accounts.google.com'
	authorise_url = 'https://%s/o/oauth2/auth?response_type=code&client_id=%%s&redirect_uri=%%s&scope=%%s' % server
	access_token_url = 'http://%s/o/oauth2/token' % server
	identity_url = 'https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s'
	post_message_url = 'http://%s/1/statuses/update.json' % server
	token_required = False
	oauth_token_GET_param = 'code'
	permissions = ('https://www.googleapis.com/auth/plus.me',)
	public = True
	can_post = False
	
	def get_authorisation_url(self):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		return self.authorise_url % (
			self.settings.get('CONSUMER_KEY'),
			'http://%s%s' % (site.domain, reverse('megaphone_callback')),
			' '.join(self.permissions)
		)
	
	def swap_tokens(self, key):
		from django.core.urlresolvers import reverse
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		resp = self.send_url(
			url = self.access_token_url,
			secure = False,
			code = key,
			client_id = self.settings.get('CONSUMER_KEY'),
			client_secret = self.settings.get('CONSUMER_SECRET'),
			redirect_uri = 'http://%s%s' % (
				site.domain, reverse('megaphone_callback')
			),
			grant_type = 'authorization_code'
		)
		
		data = simplejson.loads(resp)
		return data.get('access_token')
	
	def get_identity(self, access_token):
		data = self.open_url(self.identity_url % access_token)
		data = simplejson.loads(data)
		return data['id']
	
	def get_identity_link(self, identity):
		return 'https://plus.google.com/%s' % identity