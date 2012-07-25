from django.template import Library
from django.utils.safestring import mark_safe
from django.conf import settings
from bambu.attachments import ATTACHMENT_REGEX
from bambu.attachments.models import Attachment

WIDTH = getattr(settings, 'ATTACHMENT_WIDTH', 640)
register = Library()

@register.filter()
def attachments(value, obj, width = WIDTH):
	match = ATTACHMENT_REGEX.search(value)
	
	while not match is None and match.end() <= len(value):
		start = match.start()
		end = match.end()
		groups = match.groups()
		
		if len(groups) > 0:
			index = groups[0]
			try:
				if isinstance(obj, dict):
					inner = Attachment(
						**obj['attachments__attachment'][int(index) - 1]
					).render(width)
				else:
					inner = obj.attachments.all()[int(index) - 1].render(width)
			except IndexError:
				inner = ''
		else:
			inner = ''
		
		value = value[:start] + inner + value[end:]
		match = ATTACHMENT_REGEX.search(value, start + len(inner))
	
	return mark_safe(value)