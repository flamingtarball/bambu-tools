from django.db.models import Manager
from django.utils import simplejson
from urllib import urlencode
from urllib2 import Request, urlopen, HTTPError
from elementtree import ElementTree

class ResourceManager(Manager):
	def create_resource(self, url, width, endpoint, format):
		if format == 'json':
			mimetype = 'application/json'
		elif format == 'xml':
			mimetype = 'text/xml'
		elif format != 'html':
			raise Exception('Handler configured incorrectly (unrecognised format %s)' % format)
		
		params = {
			'url': url
		}
		
		if int(width) > 0:
			params['width'] = width
			params['maxwidth'] = width
		
		if not callable(endpoint):
			endpoint = endpoint % urlencode(params)
		
		if not callable(endpoint):
			oembed_request = Request(
				endpoint, headers = {
					'Accept': mimetype,
					'User-Agent': 'bambu-tools/2.1'
				}
			)
			
			try:
				response = urlopen(oembed_request)
			except HTTPError, ex:
				raise Exception(ex.msg)
			
			if format == 'json':
				try:
					json = simplejson.load(response)
				except:
					raise Exception('Not a JSON response')
				
				if 'html' in json:
					html = json.get('html')
				elif 'thumbnail_url' in json:
					html = '<a href="%(resource)s"><img alt=="%(title)s" src="%(url)s" /></a>' % {
						'title': json['title'],
						'url': json['thumbnail_url'],
						'resource': url,
					}
				else:
					raise Exception('Response not understood', json)
			else:
				try:
					xml = ElementTree.parse(response)
				except:
					raise Exception('Not an XML response')
				
				try:
					html = xml.getroot().find('html').text or ''
				except:
					if not xml.find('url') is None:
						html = '<a href="%(resource)s"><img alt=="%(title)s" src="%(url)s" /></a>' % {
							'title': xml.find('title') and xml.find('title').text or '',
							'url': xml.find('url').text,
							'resource': url
						}
					else:
						raise Exception('No embeddable content found')
		else:
			html = endpoint(url)
		
		return self.create(url = url, width = width, html = html)