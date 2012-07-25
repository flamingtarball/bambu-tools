from django.conf import settings as django_settings

def settings(request):
	return {
		'UPLOADIFY_URL': getattr(django_settings, 'UPLOADIFY_URL')
	}