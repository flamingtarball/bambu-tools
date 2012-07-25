from bambu.grids.grids import Grid
from bambu.grids.renderers import ModelFilterRenderer
from django.db.models import Model, Manager, ManyToManyField, Q
from django.db.models.query import QuerySet
from django.utils.datastructures import SortedDict
import shlex

class ModelGrid(Grid):
	model = None
	columns = ()
	exclude = ()
	search = ()
	filter_renderer = ModelFilterRenderer
	
	def __init__(self, request, data, *args, **kwargs):
		if isinstance(data, Model):
			queryset = data.objects.all()
		elif isinstance(data, Manager):
			queryset = data.all()
		elif isinstance(data, QuerySet):
			queryset = data
		else:
			raise ValueError('Data attribute must extend Model or QuerySet')
		
		if queryset.model != self.model:
			raise ValueError('Data queryset must match the Model defined for this ModelGrid')
		
		exclude = self.exclude or []
		super(ModelGrid, self).__init__(request, queryset, *args, **kwargs)
		
		self.empty_label = u'There are no %s in this view.' % self.model._meta.verbose_name_plural
		if not self.ordering:
			self.ordering = self.model._meta.ordering
	
	def get_columns(self):
		if not any(self.columns):
			opts = self.model._meta
			columns = []
			
			for f in opts.local_fields:
				if f != opts.pk and f.editable and not f.name in exclude:
					columns.append(f.name)
		else:
			columns = self.columns
		
		for i, column in enumerate(columns):
			if column != 'pk' and column != self.model._meta.pk.name:
				self.link_column = i
				break
		
		return columns
	
	def get_friendly_name(self, column):
		if column == '__unicode__':
			return self.model._meta.verbose_name.capitalize()
		
		if hasattr(self, column):
			func = getattr(self, column)
			if hasattr(func, 'friendly_name'):
				return func.friendly_name
		
		for f in self.model._meta.local_fields:
			if f.name == column:
				return unicode(f.verbose_name.capitalize())
		
		return super(ModelGrid, self).get_friendly_name(column)
	
	def prepare(self, obj):
		row = SortedDict()
		
		for i, column in enumerate(self.columns):
			if hasattr(obj, column):
				value = getattr(obj, column)
			elif hasattr(self, column):
				value = getattr(self, column)(obj)
			else:
				raise Exception(
					'%s not found in %s or %s' % (
						column, type(obj), type(self)
					)
				)
			
			if value and hasattr(self, 'prepare_%s' % column):
				row[column] = getattr(self, 'prepare_%s' % column)(value)
			else:
				row[column] = self._prepare_value(value)
				for field in self.model._meta.local_fields:
					if field.name == column:
						if hasattr(field, 'choices') and hasattr(obj, 'get_%s_display' % column):
							row[column] = self._prepare_value(
								getattr(obj, 'get_%s_display' % column)
							)
						
						break
		
		return row
	
	def field_is_sortable(self, field):
		if field in ('pk', '-pk', 'id', '-id'):
			return True
		
		if field.startswith('-'):
			return field[1:] in [n.name for n in self.model._meta.local_fields]
		
		return field in [n.name for n in self.model._meta.local_fields]
	
	def order(self, data):
		ordering = [
			f for f in self.ordering if self.field_is_sortable(f)
		]
		
		if isinstance(data, (Model, Manager, QuerySet)):
			return data.order_by(*ordering)
		
		return data
	
	def _validate_filters(self):
		fieldnames = [
			f.name for f in self.model._meta.local_fields
		] + [
			f.name for f in self.model._meta.local_many_to_many
		]
		
		for filter in self.filter:
			if not filter in fieldnames:
				raise Exception('Filter on unknown field "%s" not supported' % filter)
	
	def _get_filter_choices(self, filter):
		field = None
		
		for f in self.model._meta.local_fields:
			if f.name == filter:
				field = f
		
		for f in self.model._meta.local_many_to_many:
			if f.name == filter:
				field = f
		
		if field:
			return field.get_choices()
	
	def _get_search_options(self):
		values = []
		values_lowered = []
		
		for row in self.data.values_list(*self.search).distinct().order_by(*self.search):
			for column in row:
				if column and column.strip() and not column.strip().lower() in values_lowered:
					values.append(column.strip())
					values_lowered.append(column.strip().lower())
		
		return sorted(values)
	
	def perform_filter(self, data, **options):
		if isinstance(data, QuerySet):
			data = data.filter(**options)
		
		search = self._GET.get(self.prefix and '%s-search' % (self.prefix) or 'search')
		
		try:
			words = [w for w in shlex.split(str(search))]
		except:
			words = search.split(' ')
		
		if any(self.search) and search:
			q = Q()
			for column in self.search:
				for word in words:
					q |= Q(
						**{
							'%s__icontains' % column: word
						}
					)
			
			data = data.filter(q)
		
		return data