from django.views.decorators.csrf import csrf_exempt
from django.utils.functional import update_wrapper
from django.http import HttpResponse
from django.contrib.auth.models import User
from oauth.oauth import build_authenticate_header
import sys

def trim_indent(docstring):
	if not docstring:
		return ''
	
	lines = docstring.expandtabs().splitlines()
	indent = sys.maxint
	
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	
	trimmed = [lines[0].strip()]
	if indent < sys.maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	
	return '\n'.join(trimmed)

def form_initial_data(form_class, obj = None):
	initial = {}
	for (name, field) in form_class.base_fields.items():
		initial[name] = field.prepare_value(getattr(obj, name, field.initial))
	
	return initial

def wrap_api_function(site, view, detail_level, allowed_methods):
	def wrapper(request, format, *args, **kwargs):
		if not request.method in allowed_methods:
			return HttpResponse('')
		
		return site.api_view(
			view, request, format, *args,
			detail_level = detail_level + (request.method == 'POST' and 1 or 0),
			**kwargs
		)
	
	return csrf_exempt(
		update_wrapper(wrapper, view)
	)

def generate_random_key(length = 32):
	return User.objects.make_random_password(length = length)

def send_oauth_error(err):
	response = HttpResponse(err.message.encode('utf-8'))
	response.status_code = 401
	
	realm = 'OAuth'
	header = build_authenticate_header(realm=realm)
	
	for k, v in header.iteritems():
		response[k] = v
	
	return response