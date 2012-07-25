from bambu.activity.helpers import get_current_request, get_streams
from django.contrib.contenttypes.models import ContentType

def pre_save(sender, instance, **kwargs):
	if not instance.pk:
		return
	
	request = get_current_request()
	user = request and request.user.is_authenticated() and request.user or None
	if not user:
		return
	
	updates = []
	old = sender.objects.get(pk = instance.pk)
	
	fields = [
		(
			unicode(f.verbose_name),
			getattr(old, f.name),
			getattr(instance, f.name)
		) for f in sender._meta.local_fields if f.editable
	]
	
	for (name, old, new) in fields:
		if old != new:
			updates.append(name)
	
	if any(updates):
		for stream in get_streams(instance):
			stream.create_action(
				user, instance, 'updated',
				updates = updates
			)

def post_save(sender, instance, created, **kwargs):
	if not created:
		return
	
	request = get_current_request()
	user = request and request.user.is_authenticated() and request.user or None
	if not user:
		return
	
	for stream in get_streams(instance):
		stream.create_action(user, instance, 'created')

def m2m_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
	if not action in ('post_add', 'post_remove', 'post_clear'):
		return
	
	request = get_current_request()
	user = request and request.user.is_authenticated() and request.user or None
	if not user:
		return
	
	content_type = ContentType.objects.get_for_model(instance)
	
	for stream in get_streams(instance, pk_set):
		if action == 'post_add':
			stream.create_action(user, instance, 'added')
		elif action in ('post_remove', 'post_clear'):
			stream.create_action(user, instance, 'removed')

def pre_delete(sender, instance, **kwargs):
	from bambu.activity import site
	
	stream_field = site._models[sender]
	stream_model = getattr(sender, stream_field).field.rel.to
	
	request = get_current_request()
	user = request and request.user.is_authenticated() and request.user or None
	if not user:
		return
	
	for stream in get_streams(instance):
		stream.create_action(user, instance, 'deleted')