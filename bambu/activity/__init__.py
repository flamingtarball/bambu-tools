from bambu.activity.sites import ActivitySite
from bambu.activity.models import Action, Stream
from django.contrib.contenttypes.models import ContentType
import threading

_thread_locals = threading.local()
site = ActivitySite()

def add_action(stream_obj, obj, user, text_message, html_message, kind = 'custom'):
	content_type = ContentType.objects.get_for_model(stream_obj)
	stream, created = Stream.objects.get_or_create(
		content_type = content_type,
		object_id = stream_obj.pk
	)
	
	return stream.actions.create(
		user = user,
		kind = kind,
		message_plain = text_message,
		message_html = html_message,
		content_type = ContentType.objects.get_for_model(obj),
		object_id = obj.pk
	)