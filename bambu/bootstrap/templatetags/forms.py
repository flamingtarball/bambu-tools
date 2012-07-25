from django.template import Library
from django.forms.widgets import CheckboxInput
from django.forms import DateTimeField, DateField

register = Library()

@register.filter()
def is_checkbox(field):
	return isinstance(field.field.widget, CheckboxInput)
	
@register.filter()
def is_datefield(field):
	return isinstance(field.field, (DateTimeField, DateField))