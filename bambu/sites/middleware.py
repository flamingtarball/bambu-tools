from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect

DOMAIN = Site.objects.get_current().domain

class DomainRedirectMiddleware(object):
	def process_request(self, request):
		domain = request.META.get('HTTP_HOST')
		
		if domain == 'localhost' or domain.startswith('localhost:'):
			return
		
		if DOMAIN != domain:
			path = request.path
			if request.META.get('QUERY_STRING'):
				path += '?' + request.META['QUERY_STRING']
			
			return HttpResponseRedirect(
				'http://%s%s' % (DOMAIN, path)
			)