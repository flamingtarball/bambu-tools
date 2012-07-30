from bambu.megaphone.sites import MegaphoneSite
from functools import wraps
from threading import Thread

def run_async(func):
	@wraps(func)
	def async_func(*args, **kwargs):
		func_hl = Thread(target = func, args = args, kwargs = kwargs)
		func_hl.start()
		return func_hl
	
	return async_func

@run_async
def broadcast(obj, user):
	model = type(obj)
	if not model in site._registry:
		return
	
	from bambu.megaphone.models import Action
	from bambu.megaphone import helpers
	from bambu.megaphone.providers import TokenExpired
	from django.contrib.sites.models import Site
	from django.core.files import File
	import logging
	
	logger = logging.getLogger('bambu.megaphone')
	actions = Action.objects.filter(
		service__user = user,
		model = '%s.%s' % (model._meta.app_label, model._meta.module_name)
	).exclude(posts__object_id = obj.pk)
	
	if actions.count() == 0:
		logger.info(
			u'%s "%s" has already been broadcast or no actions setup' % (
				str(obj._meta.verbose_name).capitalize(),
				unicode(obj)
			)
		)
		
		return
	
	details = site._registry[model]
	title_field = details['title_field']
	image_field = details['image_field']
	media_field = details['media_field']
	url = 'http://%s%s' % (Site.objects.get_current().domain, obj.get_absolute_url())
	
	if callable(title_field):
		title = title_field(obj)
	else:
		title = getattr(obj, title_field)
	
	if image_field:
		if callable(image_field):
			image = image_field(obj)
		else:
			image = getattr(obj, image_field)
		
		if isinstance(image, File):
			image = image.url
	else:
		image = ''
	
	if media_field:
		if callable(media_field):
			media = media_field(obj)
		else:
			media = getattr(obj, media_field)
		
		if isinstance(media, File):
			media = media.url
	else:
		media = ''
	
	if image:
		image = helpers.fix_media_url(image)
	
	if media:
		media = helpers.fix_media_url(media)
	
	for action in actions:
		try:
			action.post(obj, title, url, image, media)
		except Exception, ex:
			logger.error(
				'Error posting to megaphone service %s' % action.service,
				exc_info = ex
			)

site = MegaphoneSite()