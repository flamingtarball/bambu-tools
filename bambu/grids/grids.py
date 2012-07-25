from django.core.paginator import Paginator, EmptyPage
from bambu.grids.renderers import *
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.datastructures import SortedDict
from django.db.models import Model
from urllib import urlencode
from copy import deepcopy

class Grid(object):
	per_page = 10
	paginator = Paginator
	grid_renderer = TableRenderer
	pagination_renderer = PaginationRenderer
	filter_renderer = FilterRenderer
	link_column = None
	column_attrs = ()
	actions = ()
	columns = ()
	exclude = ()
	attrs = ()
	filter = ()
	classes = ('table', 'table-striped', 'table-bordered')
	empty_label = u'There are no items in this view.'
	ordering = None
	
	def __init__(self, request, data, attrs = None, **kwargs):
		self.data = data or []
		self.attrs = attrs or {}
		classes = kwargs.get('classes') or self.classes
		attr_classes = self.attrs.get('class', '').split(' ')
		columns = []
		
		for c in classes:
			if not c in attr_classes:
				attr_classes.append(c)
		
		attr_classes.sort()
		
		self.attrs['class'] = ' '.join(attr_classes).strip()
		self.columns = self.get_columns()
		self.prefix = kwargs.get('prefix')
		
		try:
			key = self.prefix and '%s-page' % self.prefix or 'page'
			self.page = int(request.GET.get(key, ''))
		except (TypeError, ValueError):
			self.page = 1
		
		key = self.prefix and '%s-order' % self.prefix or 'order'
		if request.GET.get(key):
		 	if request.GET[key] in self.columns:
				self.ordering = (request.GET[key],)
			elif request.GET[key].startswith('-') and request.GET[key][1:] in self.columns:
				self.ordering = (request.GET[key],)
			
		self._GET = {}
		for key, value in request.GET.items():
			self._GET[key] = value
		
		self._path = request.path
	
	def get_friendly_name(self, column):
		if column in ('pk', 'id'):
			return '#'
		
		return column.replace('_', ' ').capitalize()
	
	def get_columns(self):
		if not self.columns:
			columns = []
			for item in self.data:
				if not isinstance(item, dict):
					raise Exception('Data must be a list of dicts')
			
				for key in item.keys():
					if not key in columns and not key in self.exclude:
						columns.append(key)
		else:
			columns = self.columns
		
		for i, column in enumerate(columns):
			if column != 'pk' and column != 'id':
				self.link_column = i
				break
		
		return columns
	
	def prepare(self, obj):
		row = SortedDict()
		for i, key in enumerate(self.columns):
			value = obj.get(key)
			
			if value and hasattr(self, 'prepare_%s' % key):
				row[key] = getattr(self, 'prepare_%s' % key)(value)
			else:
				row[key] = self._prepare_value(value)
		
		return row
	
	def _prepare_value(self, value):
		if isinstance(value, Model):
			try:
				return render_link(value, value.get_absolute_url())
			except:
				pass
		
		if callable(value):
			return self._prepare_value(value())
		
		if not value is None:
			return escape(unicode(value))
		
		return u''
	
	def order(self, data):
		key = self.ordering[0]
		reverse = False
		if key.startswith('-'):
			key = key[1:]
			reverse = True
		
		data = sorted(self.data, key = lambda k: k[key]) 
		if reverse:
			data.reverse()
		
		return data
	
	def field_is_sortable(self, field):
		return field in self.columns
	
	def perform_filter(self, data, **options):
		matching = []
		for item in data:
			for key, value in options:
				if not unicode(item.get(key)) == unicode(value):
					continue
			
			matching.append(matching)
		
		return matching
	
	@property
	def renderable_data(self):
		if not hasattr(self, '_renderable_data'):
			fieldnames = [
				(n, self.prefix and '%s-%s' % (self.prefix, n) or n)
				for n in self.filter
			]
			
			options = {}
			for (realname, getname) in fieldnames:
				if self._GET.get(getname):
					options[realname] = self._GET[getname]
			
			data = self.perform_filter(self.data, **options)
			
			if self.ordering and any(self.ordering):
				data = self.order(data)
			
			self._paginator = self.paginator(data, self.per_page)
			
			try:
				self._page = self._paginator.page(self.page)
			except EmptyPage:
				self._page = self._paginator.page(1)
			
			self._renderable_data = self._page.object_list
		return self._renderable_data
	
	def render(self):
		return mark_safe(
			self.grid_renderer(self).render(self.attrs)
		)
	
	def pagination(self):
		return mark_safe(
			self.pagination_renderer(self).render(self._page)
		)
	
	def filtering(self):
		self._validate_filters()
		return mark_safe(
			self.filter_renderer(self).render(self._GET)
		)
	
	def _validate_filters(self):
		for filter in self.filter:
			if not filter in self.columns:
				raise Exception('Filter on unknown column "%s" not supported' % filter)
	
	def _get_filter_choices(self, filter):
		choices = []
		for item in self.data:
			value = item.get(filter)
			if value and not value in choices:
				choices.add(Value)
		
		return [(c, c) for c in choices]
	
	def _context_sensitive_url(self, **kwargs):
		get = deepcopy(self._GET)
		get.update(kwargs)
		
		return self._path + '?' + urlencode(get)
	
	def __unicode__(self):
		return self.filtering() + self.render() + self.pagination()