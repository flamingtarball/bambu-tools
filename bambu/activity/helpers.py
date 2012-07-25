from bambu.activity.models import Stream
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField

def get_current_request():
	from bambu.activity import _thread_locals
	
	return getattr(_thread_locals, 'request', None)

def get_streams(instance, m2m_pks = None):
	from bambu.activity import site
	
	model = type(instance)
	if model in site._registry:
		object_ids = [instance.pk]
	else:
		stream_field = site._models[model]
		field = getattr(model, stream_field).field
		
		if isinstance(field, ForeignKey):
			model, object_ids = field.rel.to, [getattr(instance, stream_field).pk]
		elif isinstance(field, ManyToManyField):
			if not m2m_pks is None:
				model, object_ids = field.rel.to, m2m_pks
			else:
				model = field.rel.to
				object_ids = field.rel.to.objects.filter(
					**{
						field.rel.related_name: instance
					}
				).distinct().values_list('pk', flat = True)
		else:
			exit
	
	content_type = ContentType.objects.get_for_model(model)
	for object_id in object_ids:
		stream, created = Stream.objects.get_or_create(
			content_type = content_type,
			object_id = object_id
		)
		
		yield stream