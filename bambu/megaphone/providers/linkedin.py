from bambu.megaphone.providers import OAuthProviderBase
from elementtree import ElementTree

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<share>
  <content>
    <title>{{ message }}</title>
    <submitted-url>{{ url }}</submitted-url>
    <submitted-image-url>{{ image }}</submitted-image-url>
  </content>
  <visibility>
    <code>anyone</code>
  </visibility>
</share>"""

class LinkedInProvider(OAuthProviderBase):
	verbose_name = 'LinkedIn'
	server = 'api.linkedin.com'
	request_token_url = 'https://%s/uas/oauth/requestToken' % server
	authorise_url = 'https://%s/uas/oauth/authorize' % server
	access_token_url = 'https://%s/uas/oauth/accessToken' % server
	identity_url = 'http://%s/v1/people/~' % server
	post_message_url = 'http://%s/v1/people/~/shares' % server
	use_ssl = True
	
	def parse_identity(self, data):
		data = ElementTree.parse(data)
		return '%s %s' % (
			data.find('first-name').text, data.find('last-name').text
		)
	
	def post_message(self, access_token, message, url, image = None, media = None):
		from django.template import Template, Context
		
		xml = Template(XML_TEMPLATE).render(
			Context(
				dict(
					message = message,
					url = url,
					image = image or ''
				)
			)
		)
		
		self.post_url(self.post_message_url, access_token, xml)
		return access_token