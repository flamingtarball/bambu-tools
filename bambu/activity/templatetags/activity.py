from django.template import Library
from django.contrib.contenttypes.models import ContentType
from bambu.activity.models import Stream

register = Library()

@register.inclusion_tag('activity/stream.inc.html', takes_context = True)
def stream(context, obj = None, condensed = False):
	request = context.get('request')
	if not request or request.user.is_anonymous():
		return
	
	if obj:
		streams = Stream.objects.filter(
			content_type = ContentType.objects.get_for_model(obj),
			object_id = obj.pk
		)
	else:
		streams = Stream.objects.get_for_user(request.user)
	
	return {
		'streams': streams,
		'show_headers': obj is None,
		'condensed': condensed == 'condensed'
	}