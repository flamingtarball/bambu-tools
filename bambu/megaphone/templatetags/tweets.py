from django.template import Library
from django.utils.safestring import mark_safe
import re

register = Library()

@register.filter
def usernames(value):
	value = re.sub(r'(?P<prefix> )@(?P<username>\w+)', '\g<prefix>@<a href="http://twitter.com/\g<username>/" target="_blank">\g<username></a>', value)
	value = re.sub(r'^@(?P<username>\w+)', '@<a href="http://twitter.com/\g<username>/" target="_blank">\g<username></a>', value)
	
	return mark_safe(value)

@register.filter
def hashtags(value):
	value = re.sub(r'(?P<prefix> )#(?P<tag>[^\d]\w+)', '\g<prefix><a href="http://search.twitter.com/search?tag=\g<tag>" rel="external">#\g<tag></a>', value)
	value = re.sub(r'^#(?P<tag>[^\d]\w+)', '<a href="http://search.twitter.com/search?tag=\g<tag>" rel="external">#\g<tag></a>', value)
	
	return mark_safe(value)