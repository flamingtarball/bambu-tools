from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils import simplejson
from django import forms
from urllib import urlencode

def flatten_attrs(attrs):
	portions = []
	for key, value in attrs.items():
		portions.append(' %s="%s"' % (key, value))
	
	return ''.join(portions)

def render_link(value, url, attrs = {}, safe = False):
	return u'<a href="%s"%s>%s</a>' % (
		url, flatten_attrs(attrs), safe and unicode(value) or escape(unicode(value))
	)

class Renderer(object):
	container_tag = 'div'
	item_container_tag = 'dl'
	item_column_tag = 'dt'
	item_value_tag = 'dd'
	
	def __init__(self, grid):
		self.grid = grid
	
	def render_header(self, attrs):
		portions = [u'<%s' % self.container_tag]
		portions.append(flatten_attrs(attrs))
		portions.append('>')
		return ''.join(portions)
	
	def render_footer(self):
		return u'</%s>' % self.container_tag
	
	def render_value(self, index, value, raw_data):
		if index == self.grid.link_column:
			if hasattr(raw_data, 'get_absolute_url'):
				return render_link(value, raw_data.get_absolute_url())
			
			if hasattr(self.grid, 'get_absolute_url'):
				return render_link(value, self.grid.get_absolute_url(raw_data))
		
		return value
	
	def render_item(self, raw_data, prepared_data, attrs):
		portions = [u'<%s' % self.item_container_tag]
		portions.append(u'>')
		
		for i, (key, value) in enumerate(prepared_data.items()):
			if self.grid.column_attrs:
				attrs = self.grid.column_attrs[i] or {}
			else:
				attrs = {}
			
			portions.append(
				u'<%(tag)s>%(attrs)s%(key)s</%(tag)s>' % {
					'tag': self.item_column_tag,
					'attrs': flatten_attrs(attrs),
					'key': self.grid.get_friendly_name(key)
				}
			)
			
			portions.append(
				u'<%(tag)s>%(value)s</%(tag)s>' % {
					'tag': self.item_value_tag,
					'value': self.render_value(i, value, raw_data)
				}
			)
		
		portions.append(u'</%s>' % self.item_container_tag)
		for action in self.grid.actions:
			portions.append(self.render_action(action, raw_data))
		
		return u''.join(portions)
	
	def render_action(self, action, obj):
		func = getattr(self.grid, action)
		label = getattr(func, 'friendly_name', action.replace('_', ' ').capitalize())
		url = func(obj)
		
		if hasattr(func, 'attrs'):
			attrs = func.attrs
		else:
			attrs = {}
		
		if hasattr(func, 'classes'):
			classes = func.classes
		else:
			classes = (attrs.get('class') or 'btn').split(' ')
		
		attrs['class'] = ' '.join(classes)
		
		if hasattr(func, 'icon'):
			colour = ''
			if hasattr(func, 'icon_colour'):
				colour = ' icon-%s' % func.icon_colour
			
			label = u'<span class="icon-%s%s"></span> %s' % (func.icon, colour, escape(label))
		else:
			label = escape(label)
		
		return render_link(label, url, attrs, True)
	
	def render_empty(self):
		return u'<div>%s</div>' % self.grid.empty_label
	
	def render(self, attrs):
		portions = [self.render_header(attrs)]
		
		if any(self.grid.renderable_data):
			for raw in self.grid.renderable_data:
				prepared = self.grid.prepare(raw)
				portions.append(self.render_item(raw, prepared))
		else:
			portions.append(self.render_empty())
		
		portions.append(self.render_footer())
		return u''.join(portions)

class TableRenderer(Renderer):
	container_tag = 'table'
	item_container_tag = 'tr'
	item_column_tag = 'th'
	item_value_tag = 'td'
	
	def render_sort_field(self, key):
		sortkey = self.grid.prefix and '%s-order' % (self.grid.prefix) or 'order'
		attrs = {}
		sortable = self.grid.field_is_sortable(key)
		
		if sortable:
			if self.grid.ordering and key in self.grid.ordering:
				urlkey = '-%s' % key
				attrs['class'] = 'order-field active'
			elif self.grid.ordering:
				ordering = [
					f.startswith('-') and f[1:] or f
					for f in self.grid.ordering
				]
				
				if key in ordering:
					urlkey = '%s' % key
					attrs['class'] = 'order-field order-reverse active'
				else:
					urlkey = key
			else:
				urlkey = key
		
		portions = [u'<%s%s>' % (self.item_column_tag, flatten_attrs(attrs))]
		
		if sortable:
			portions.append(
				u'<a href="%s">' % self.grid._context_sensitive_url(
					**{
						sortkey: urlkey
					}
				)
			)
		
		portions.append(self.grid.get_friendly_name(key))
		
		if sortable:
			portions.append(u'</a>')
		
		portions.append(u'</%s>' % self.item_column_tag)
		return u''.join(portions)
	
	def render_header(self, attrs):
		portions = [super(TableRenderer, self).render_header(attrs)]
		portions.append('<thead><tr>')
		
		for key in self.grid.columns:
			portions.append(self.render_sort_field(key))
		
		if any(self.grid.actions):
			portions.append(
				u'<%(tag)s>Actions</%(tag)s>' % {
					'tag': self.item_column_tag
				}
			)
		
		portions.append('</tr></thead><tbody>')
		return u''.join(portions)
	
	def render_item(self, raw_data, prepared_data):
		portions = [u'<%s' % self.item_container_tag]
		portions.append(u'>')
		
		for i, (key, value) in enumerate(prepared_data.items()):
			if self.grid.column_attrs:
				attrs = self.grid.column_attrs[i] or {}
			else:
				attrs = {}
			
			portions.append(
				u'<%(tag)s%(attrs)s>%(value)s</%(tag)s>' % {
					'tag': self.item_value_tag,
					'attrs': flatten_attrs(attrs),
					'value': self.render_value(i, value, raw_data)
				}
			)
		
		if any(self.grid.actions):
			portions.append(u'<%s>' % self.item_value_tag)
			actions = []
			for action in self.grid.actions:
				actions.append(
					self.render_action(action, raw_data)
				)
			
			portions.append(u' '.join(actions))
			portions.append(u'</%s>' % self.item_value_tag)
		
		portions.append(u'</%s>' % self.item_container_tag)
		return u''.join(portions)
	
	def render_empty(self):
		cols = len(self.grid.columns) + (any(self.grid.actions) and 1 or 0)
		return u'<tr class="empty"><td colspan="%d">%s</td></tr>' % (cols, self.grid.empty_label)
	
	def render_footer(self):
		return u'</tbody>' + super(TableRenderer, self).render_footer()

class PaginationRenderer(object):
	def __init__(self, grid):
		self.grid = grid
	
	def render(self, page):
		if page.has_other_pages():
			key = self.grid.prefix and '%s-page' % self.grid.prefix or 'page'
			portions = [u'<div class="pagination"><ul>']
			
			if page.has_previous():
				portions.append(
					u'<li class="prev"><a href="%s">&larr; Previous</a></li>' % self.grid._context_sensitive_url(
						**{key: page.previous_page_number()}
					)
				)
			else:
				portions.append(u'<li class="prev disabled"><a>&larr; Previous</a></li>')
			
			for i in page.paginator.page_range:
				portions.append(
					u'<li class="next"><a href="%s">%d</a></li>' % (
						self.grid._context_sensitive_url(
							**{key: i}
						), i
					)
				)
			
			if page.has_next():
				portions.append(
					u'<li class="next"><a href="%s">Next &rarr;</a></li>' % self.grid._context_sensitive_url(
						**{key: page.next_page_number()}
					)
				)
			else:
				portions.append(u'<li class="next disabled"><a>Next &rarr;</a></li>')
			
			portions.append(u'</ul></div>')
			return ''.join(portions)
	
		return ''

class FilterRenderer(object):
	def __init__(self, grid):
		self.grid = grid
	
	def render(self, data, attrs = None):
		if not attrs:
			attrs = {
				'class': 'form-inline clearfix'
			}
		
		attrs['id'] = attrs.get('id',
			self.grid.prefix and ('%s-filterform' % self.grid.prefix) or 'filterform'
		)
		
		portions = ['<form %s>' % flatten_attrs(attrs)]
		portions.append(self._render_fields(data))
		portions.append(self._render_hiddenfields(data))
		portions.append('</form>')
		portions.append(self._render_script(attrs['id']))
		
		return ''.join(portions)
	
	def _get_fieldnames(self):
		return [
			self.grid.prefix and '%s-%s' % (self.grid.prefix, n) or n
			for n in self.grid.filter
		]
	
	def _render_fields(self, data):
		fields = ''
		
		for fieldname in self.grid.filter:
			name = self.grid.prefix and '%s-%s' % (self.grid.prefix, fieldname) or fieldname
			value = data.get(name)
			choices = self.grid._get_filter_choices(fieldname)
			
			field = forms.ChoiceField(choices = choices)
			field.widget.choices = [
				('', '--- %s ---' % self.grid.get_friendly_name(fieldname))
			] + field.widget.choices[1:]
			
			fields += field.widget.render(name, value)
		
		return fields
	
	def _render_hiddenfields(self, data):
		preserve = {}
		for key, value in data.items():
			if not key in self._get_fieldnames():
				preserve[key] = value
		
		portions = []
		for item in preserve.items():
			portions.append('<input type="hidden" name="%s" value="%s" />' % item)
		
		return ''.join(portions)
	
	def _render_script(self, form_id):
		portions = []
		
		portions.append('<script>$(document).ready(function() { ')
		portions.append("$('form#%s :input').bind('change'," % form_id)
		portions.append("function(e) { $(this).closest('form').submit();});")
		portions.append('});</script>')
		
		return ''.join(portions)

class ModelFilterRenderer(FilterRenderer):
	def _get_fieldnames(self):
		return [
			self.grid.prefix and '%s-%s' % (self.grid.prefix, n) or n
			for n in self.grid.filter
		] + [
			self.grid.prefix and '%s-search' % (self.grid.prefix) or 'search'
		]
	
	def _render_fields(self, data):
		fields = ''
		if any(self.grid.search):
			name = self.grid.prefix and '%s-search' % (self.grid.prefix) or 'search'
			value = data.get(name)
			
			fields += u'<input name="%(name)s" id="id_%(name)s" type="text"' % {'name': name}
			
			if value:
				fields += u' value="%s"' % value
			
			fields += u' class="pull-right" placeholder="Search %(model)s" autocomplete="off" />' % {
				'model': unicode(self.grid.model._meta.verbose_name_plural)
			}
		
		return fields + super(ModelFilterRenderer, self)._render_fields(data)
	
	def _render_script(self, form_id):
		portions = [super(ModelFilterRenderer, self)._render_script(form_id)]
		
		if any(self.grid.search):
			search_id = self.grid.prefix and '%s-search' % (self.grid.prefix) or 'search'
			
			portions.append('<script>$(document).ready(function() { ')
			portions.append(
				"$('form#%s input#id_%s').typeahead({source: %s});" % (
					form_id, search_id, simplejson.dumps(self.grid._get_search_options())
				)
			)
			
			portions.append('});</script>')
		
		return ''.join(portions)