from django.utils.importlib import import_module
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from bambu.payments import states
from urllib import quote_plus, urlopen
from httplib2 import Http
import socket, logging, copy

HTTP_TIMEOUT = 15

class GatewayAPICall(object):
	def __init__(self, url):
		self._url = url
		self._params = ''
	
	def param(self, key, value):
		if self._params:
			self._params += '&'
		
		self._params += quote_plus(key) + '=' + quote_plus(unicode(value))
	
	def _parse(self, stream):
		return stream.read()
	
	def GET(self):
		url = '%s?%s' % (
			self._url,
			self._params
		)
		
		self.logger = logging.getLogger()
		self.logger.info(url)
		
		return self._parse(urlopen(url))
	
	def POST(self):
		http = Http()
		resp, content = http.request(self._url, 'PUT', self._params)
		
		return content

class Gateway(object):
	logo = ''
	verbose_name = 'Payment gateway'
	credentials = {}
	live = False
	
	def __init__(self, live, credentials, shortname):
		self.live = live
		if any(credentials):
			self.credentials = credentials
		
		self.shortname = shortname
		self.logger = logging.getLogger()
	
	def _api(self):
		return GatewayAPICall('')
	
	def _cancel_url(self, payment, ssl = False):
		site = Site.objects.get_current()
		return 'http%s://%s%s' % (
			ssl and 's' or '',
			site.domain,
			reverse('payment_cancel', args = [payment.pk])
		)
	
	def _callback_url(self, payment, ssl = False):
		site = Site.objects.get_current()
		return 'http%s://%s%s' % (
			ssl and 's' or '',
			site.domain,
			reverse('payment_callback', args = [payment.pk])
		)
	
	def _message_user(self, request, payment, success = True, message = ''):
		from django.contrib import messages
		
		messages.add_message(
			request,
			success and messages.SUCCESS or messages.ERROR,
			message or u'Your %s has been %s successfully.' % (
				payment.recurring and 'subscription' or 'payment',
				payment.recurring and 'setup' or 'made'
			)
		)
	
	def _success(self, request, payment, remote_id):
		from django.template.response import TemplateResponse
		
		payment.statuses.create(
			state = states.PAYMENT_COMPLETE,
			label = u'Billing agreement setup'
		)
		
		payment.remote_id = remote_id
		payment.save()
		
		self._message_user(request, payment)
		return TemplateResponse(
			request,
			'payments/complete.html',
			{
				'payment': payment,
				'gateway': self
			}
		)
	
	def _cancel(self, request, payment):
		from django.http import HttpResponseRedirect
		from django.template.response import TemplateResponse
		
		payment.statuses.create(
			state = states.PAYMENT_CANCELLED,
			label = u'Billing agreement cancelled'
		)
		
		self._message_user(request, payment, False,
			u'Your %s has not been %s.' % (
				payment.recurring and 'subscription' or 'payment',
				payment.recurring and 'setup' or 'made'
			)
		)
		
		return TemplateResponse(
			request,
			'payments/cancelled.html',
			{
				'payment': payment,
				'gateway': self
			}
		)
	
	def _authorise(self, request, payment, redirect):
		from django.http import HttpResponseRedirect

		payment.statuses.create(
			state = states.PAYMENT_AUTHORISING,
			label = u'Authorising payment'
		)

		return HttpResponseRedirect(redirect)
	
	def create_view(self, request, payment):
		raise NotImplementedError('Method not implemented.')

	def authorise_view(self, request, payment, **kwargs):
		raise NotImplementedError('Method not implemented.')
	
	def cancel_view(self, request, payment, **kwargs):
		return self._cancel(request, payment)
	
	def callback_view(self, request):
		raise NotImplementedError('Method not implemented.')

class GatewayException(Exception):
	pass

def autodiscover():
	from bambu.payments import site
	
	gateways = {}
	live = getattr(settings, 'PAYMENTS_ACCEPT_REAL', False)
	
	for (gateway, shortname) in getattr(settings, 'PAYMENT_GATEWAYS', []):
		dot = gateway.rfind('.')
		mod = import_module(gateway[:dot])
		klass = getattr(mod, gateway[dot + 1:])
		credentials = getattr(
			settings, 'PAYMENET_GATEWAY_CREDENTIALS', {}
		).get(gateway[dot + 1:])
		
		credentials = credentials and credentials.get(live and 'LIVE' or 'TEST') or {}
		gateways[gateway] = klass(live, credentials or {}, shortname)
	
	site._gateways = gateways