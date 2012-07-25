from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.template.response import TemplateResponse
from bambu.megaphone.models import Service, Action, Post, Link, Click
from bambu.megaphone import helpers
from hashlib import md5
import logging

@login_required
def auth(request):
	try:
		name = request.GET.get('provider')
		provider = helpers.get_provider(name, True)
	except (ImportError, AttributeError):
		raise Http404('Provider %s not found.' % request.GET.get('provider'))
	
	if provider.token_required:
		token, auth_url = provider.get_token_and_auth_url()
		
		if token:
			request.session['unauthed_token'] = token.to_string()
		else:
			request.session['unauthed_token'] = None
	else:
		auth_url = provider.get_authorisation_url()
	
	if 'input_id' in request.GET:
		request.session['preauth_url'] = '::oauth;id=%s' % request.GET['input_id']
	else:
		request.session['preauth_url'] = request.META.get('HTTP_REFERER', '/')
	
	request.session['oauth_provider'] = name
	request.session.modified = True
	
	return HttpResponseRedirect(auth_url)

@login_required
def deauth(request):
	try:
		name = request.GET.get('provider')
		provider = helpers.get_provider(name, True)
	except (ImportError, AttributeError):
		raise Http404('Provider %s not found.' % request.GET.get('provider'))
	
	request.user.megaphone_services.filter(provider = name).delete()
	messages.success(request, 'You\'ve been disconnected from %s.' % provider.verbose_name)
	preauth_url = request.session.get('preauth_url', '/')
	
	return HttpResponseRedirect(preauth_url)

@login_required
def callback(request):
	logger = logging.getLogger('bambu.megaphone')
	
	try:
		name = request.session.get('oauth_provider')
		provider = helpers.get_provider(name, True)
	except (ImportError, AttributeError):
		raise Http404('Provider %s not found.' % request.session.get('oauth_provider'))
	
	preauth_url = request.session.get('preauth_url', '/')
	if request.GET.get('error_reason'):
		if preauth_url.startswith('::oauth'):
			input_id = preauth_url[preauth_url.find(';id=') + 4:]
			response = HttpResponse("""<!DOCTYPE html><html><head></head><body>
				<script>opener.document.getElementById('%(input_id)s').value = '';
				window.close();
				</script></body></html>""" % {
					'input_id': input_id,
				}
			)
		else:
			response = HttpResponseRedirect(preauth_url)
		
		return response
	
	authed_token = request.GET.get(provider.oauth_token_GET_param, 'no-token')
	if provider.token_required:
		unauthed_token = request.session.get('unauthed_token', None)
		if unauthed_token and not provider.verify_auth_token(unauthed_token, authed_token):
			messages.error(request,
				'It wasn\'t possible to complete your connection to %s.' % provider.verbose_name
			)
			
			return HttpResponseRedirect(preauth_url)
		
		access_token = provider.verify_and_swap(request)
	else:
		access_token = provider.swap_tokens(authed_token)
	
	if preauth_url.startswith('::oauth'):
		input_id = preauth_url[preauth_url.find(';id=') + 4:]
		return HttpResponse("""<!DOCTYPE html><html><head></head><body>
			<script>opener.document.getElementById('%(input_id)s').value = '%(value)s';
			opener.document.getElementById('%(input_id)s_link').innerHTML = 'Connected to %(name)s';
			opener.document.getElementById('%(input_id)s_link').setAttribute('disabled', 'disabled');
			opener.document.getElementById('%(input_id)s_link').removeAttribute('href');
			window.close();
			</script></body></html>""" % {
				'input_id': input_id,
				'value': access_token,
				'name': provider.verbose_name
			}
		)
	else:
		request.user.megaphone_services.create(
			provider = name,
			access_token = unicode(access_token)
		)
		
		messages.success(request, 'You are now successully connected to %s.' % provider.verbose_name)
		return HttpResponseRedirect(preauth_url)

@login_required
def connect(request):
	from bambu.megaphone import site
	from copy import deepcopy
	
	providers = helpers.get_provider_choices()
	actions = []
	services = request.user.megaphone_services.values_list('provider', 'identity')
	identities = {}
	
	staff = request.user.is_staff
	for (klass, details) in site._registry.items():
		if not details['staff_only'] or (staff and details['staff_only']):
			actions.append(
				{
					'name': '%s.%s' % (klass._meta.app_label, klass._meta.module_name),
					'verbose_name': details['verb']
				}
			)
	
	for (provider, identity) in services:
		identities[provider] = identity
	
	connections = []
	
	for (name, verbose) in providers:
		service_actions = deepcopy(actions)
		for action in service_actions:
			try:
				enabled_action = Action.objects.get(
					service__user = request.user,
					service__provider = name,
					model = action['name']
				)
				
				action['enabled'] = True
				action['template'] = enabled_action.message_template
			except Action.DoesNotExist:
				pass
		
		connections.append(
			{
				'name': name,
				'verbose_name': verbose,
				'connected': name in identities,
				'identity': identities.get(name),
				'actions': service_actions
			}
		)
	
	return TemplateResponse(
		request,
		'megaphone/connect.html',
		{
			'connections': connections,
			'breadcrumb_trail': (
				(reverse('home'), u'Home'),
				(reverse('profile'), u'My profile'),
				('', 'Connect')
			),
			'title_parts': ('Connections', 'My profile')
		}
	)

@login_required
def connect_add_action(request):
	provider = request.GET.get('provider')
	model = request.GET.get('model')
	
	try:
		service = request.user.megaphone_services.get(provider = provider)
	except Service.DoesNotExist:
		raise Http404('No connection to service')
	
	if service.actions.filter(model = model).count() == 0:
		service.actions.create(model = model)
	else:
		raise Http404('Action already registered')
	
	if request.is_ajax():
		return HttpResponse('OK')
	else:
		messages.success(request, 'This action has been successfully added.');
		return HttpResponseRedirect(reverse('profile_connect'))

@login_required
def connect_delete_action(request):
	provider = request.GET.get('provider')
	model = request.GET.get('model')
	
	try:
		service = request.user.megaphone_services.get(provider = provider)
	except Service.DoesNotExist:
		raise Http404('No connection to service')
	
	if service.actions.filter(model = model).count() > 0:
		service.actions.filter(model = model).delete()
	else:
		raise Http404('Action not registered')
	
	if request.is_ajax():
		return HttpResponse('OK')
	else:
		messages.success(request, 'This action has been successfully removed.');
		return HttpResponseRedirect(reverse('profile_connect'))

def track_link(request, pk):
	link = get_object_or_404(Link, pk = pk)
	ip = request.META.get('REMOTE_ADDR')
	
	if ip:
		ip = md5(ip)
		
		try:
			click = link.clicks.get(ip = ip)
			click.click_count += 1
			click.save()
		except Click.DoesNotExist:
			click = link.clicks.create(ip = ip)
	
	return HttpResponseRedirect(link.url)