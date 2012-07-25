from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from bambu.preview.models import Preview

@login_required
def preview(request, pk):
	preview = get_object_or_404(Preview, pk = pk, creator = request.user)
	obj = preview.make_object()
	
	return TemplateResponse(
		request,
		(
			'preview/%s/%s.html' % (
				preview.content_type.app_label, preview.content_type.model
			),
			'preview/%s/object.html' % preview.content_type.app_label,
			'preview/object.html',
		),
		{
			'obj': obj,
			'content_type': preview.content_type
		}
	)