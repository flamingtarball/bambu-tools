from httplib import HTTPConnection, HTTPSConnection
from oauth.oauth import OAuthConsumer, OAuthSignatureMethod_HMAC_SHA1, OAuthRequest, OAuthToken
from urllib import urlopen, urlencode

class TokenExpired(Exception):
	def __init__(self, provider, *args, **kwargs):
		super(TokenExpired, self).__init__(*args, **kwargs)
		self.provider = provider

class ProviderBase(object):
	verbose_name = 'Provider'
	server = ''
	use_trackable_urls = True
	use_ssl = True
	public = False
	can_post = True
	channels = ()
	
	def __init__(self, **kwargs):
		self.settings = kwargs
	
	def make_link(self, url):
		from bambu.megaphone.models import Link
		from django.contrib.sites.models import Site
		
		site = Site.objects.get_current()
		
		try:
			link = Link.objects.get(url = url)
		except Link.DoesNotExist:
			link = Link.objects.create(url = url)
		
		return 'http://%s%s' % (site.domain, link.get_absolute_url())
	
	def fetch_response(self, request, connection):
		url = request.to_url()
		start = 'http://%s' % self.server
		if url.startswith(start):
			url = url[len(start):]
		
		start = 'https://%s' % self.server
		if url.startswith(start):
			url = url[len(start):]
		
		connection.request(request.http_method, url)
		response = connection.getresponse()
		return response.read()
	
	def get_identity_link(self, identity):
		return 'http://%s/%s' % (self.server, identity)
	
	def fetch_url(self, url, token, **kwargs):
		from StringIO import StringIO
		
		token = OAuthToken.from_string(str(token))
		consumer = self.get_consumer()
		connection = self.get_connection(False)
		
		request = OAuthRequest.from_consumer_and_token(
			consumer, token = token, http_method = 'GET',
			http_url = url, parameters = kwargs
		)
		
		request.sign_request(self.signature_method, consumer, token)
		url = request.to_url()
		start = 'http://%s' % self.server
		
		if url.startswith(start):
			url = url[len(start):]
		
		start = 'https://%s' % self.server
		if url.startswith(start):
			url = url[len(start):]
		
		connection.request(request.http_method, url, '', request.to_header())
		resp = connection.getresponse().read()
		return StringIO(resp)
	
	def get_identity(self, access_token):
		return self.parse_identity(
			self.fetch_url(self.identity_url, access_token)
		)
	
	def get_connection(self, secure = True):
		server, colon, port = self.server.partition(':')
		if port:
			port = int(port)
		else:
			port = secure and 443 or 80
		
		klass = secure and HTTPSConnection or HTTPConnection
		return klass(server, port)
	
	def open_url(self, url):
		return urlopen(url).read()
	
	def send_url(self, url, secure = True, **data):
		connection = self.get_connection()
		
		if url.startswith('http://'):
			url = url[len('http://'):]
		elif url.startswith('https://'):
			url = url[len('https://'):]
		
		slash = url.find('/')
		if slash > -1:
			url = url[slash:]
		else:
			url = '/'
		
		connection.request('POST', url, urlencode(data),
			{
				'Content-Type': 'application/x-www-form-urlencoded'
			}
		)
		
		response = connection.getresponse()
		return response.read()
	
	def post_message(self, access_token, message, url, image = None):
		raise NotImplementedError('Method not implemented.')
	
	def get_channels(self):
		for channel in self.channels:
			yield (
				'%s.%s.get_%s_items' % (self.__module__, type(self).__name__, channel),
				channel.capitalize().replace('_', ' ')
			)

class OAuthProviderBase(ProviderBase):
	verbose_name = 'OAuth Provider'
	request_token_url = ''
	authorise_url = ''
	access_token_url = ''
	identity_url = ''
	post_message_url = ''
	token_required = True
	signature_method = OAuthSignatureMethod_HMAC_SHA1()
	oauth_token_GET_param = 'oauth_token'
	oauth_verifier_GET_param = 'oauth_verifier'
		
	def get_consumer(self):
		return OAuthConsumer(
			self.settings.get('CONSUMER_KEY'),
			self.settings.get('CONSUMER_SECRET')
		)
	
	def get_token_and_auth_url(self):
		connection = self.get_connection(self.use_ssl)
		consumer = self.get_consumer()
		token = self.get_unauthorised_request_token(consumer, connection)
		url = self.get_authorisation_url(consumer, token)
		
		return token, url
	
	def verify_and_swap(self, request):
		return self.swap_tokens(
			self.get_consumer(),
			request.session.get('unauthed_token'),
			oauth_verifier = request.GET.get(self.oauth_verifier_GET_param)
		)
	
	def get_unauthorised_request_token(self, consumer, connection):
		from django.contrib.sites.models import Site
		from django.core.urlresolvers import reverse
		
		request = OAuthRequest.from_consumer_and_token(
			consumer, http_url = self.request_token_url,
			parameters = {
				'oauth_callback': 'http://%s%s' % (
					Site.objects.get_current().domain, reverse('megaphone_callback')
				)
			}
		)
		
		request.sign_request(self.signature_method, consumer, None)
		resp = self.fetch_response(request, connection)
		token = OAuthToken.from_string(resp)
		return token
	
	def get_authorisation_url(self, consumer = None, token = None):
		if self.token_required and (not consumer and not token):
			raise Exception('Consumer and token are required')
		
		oauth_request = OAuthRequest.from_consumer_and_token(
			consumer, token = token, http_url = self.authorise_url
		)
		
		oauth_request.sign_request(self.signature_method, consumer, token)
		return oauth_request.to_url()
	
	def verify_auth_token(self, unauthed_token, auth_token):
		token = OAuthToken.from_string(unauthed_token)
		return token.key == auth_token
	
	def swap_tokens(self, *args, **kwargs):
		if self.token_required:
			consumer, token = args
			token = OAuthToken.from_string(token)
			
			request = OAuthRequest.from_consumer_and_token(
				consumer, token = token,
				http_url = self.access_token_url,
				parameters = kwargs
			)
			
			request.sign_request(self.signature_method, consumer, token)
			url = request.to_url()
			
			if url.startswith('http://'):
				url = url[7:]
			elif url.startswith('https://'):
				url = url[8:]
			
			if url.startswith(self.server):
				url = url[len(self.server):]
			
			q = url.find('?')
			if q > 01:
				qs = url[q + 1:]
				url = url[:q]
			else:
				qs = ''
			
			connection = self.get_connection(False)
			connection.request(request.http_method, url, qs, request.to_header())
			
			resp = connection.getresponse().read()
			return OAuthToken.from_string(resp)
		else:
			raise NotImplementedError('Method not implemented for non-standard OAuth provider.')
	
	def get_url(self, url, token, *args, **kwargs):
		from StringIO import StringIO
		
		token = OAuthToken.from_string(str(token))
		consumer = self.get_consumer()
		connection = self.get_connection(False)
		
		request = OAuthRequest.from_consumer_and_token(
			consumer, token = token, http_method = 'GET',
			http_url = url, parameters = kwargs
		)
		
		request.sign_request(self.signature_method, consumer, token)
		url = request.to_url()
		
		connection.request(
			request.http_method,
			url,
			''.join(args)
		)
		
		resp = connection.getresponse().read()
		return StringIO(resp)
	
	def post_url(self, url, token, *args, **kwargs):
		from StringIO import StringIO
		
		token = OAuthToken.from_string(str(token))
		consumer = self.get_consumer()
		connection = self.get_connection(False)
		
		request = OAuthRequest.from_consumer_and_token(
			consumer, token = token, http_method = 'POST',
			http_url = url, parameters = kwargs
		)
		
		request.sign_request(self.signature_method, consumer, token)
		connection.request(
			request.http_method,
			request.to_url(),
			''.join(args)
		)

		resp = connection.getresponse().read()
		return StringIO(resp)