from django.db.models import Manager
from django.utils import simplejson

class TaskManager(Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
	
	def create_task(self, func, date = None,
		success_callback = None, success_callback_args = None, success_callback_kwargs = None,
		failure_callback = None, failure_callback_args = None, failure_callback_kwargs = None,
		*args, **kwargs
	):
		if getattr(func, '__module__', ''):
			f = '%s.%s' % (func.__module__, func.__name__)
		else:
			f = func.__name__
		
		obj = self.model(
			scheduled_for = date,
			function = str(f),
			arguments = simplejson.dumps(args),
			keyword_arguments = simplejson.dumps(kwargs)
		)
		
		if success_callback:
			if getattr(success_callback, '__module__', ''):
				f = '%s.%s' % (success_callback.__module__, success_callback.__name__)
			else:
				f = callback.__name__
			
			obj.success_callback_function = f
			
			if success_callback_args and any(success_callback_args):
				obj.success_callback_arguments = simplejson.dumps(success_callback_args)
			
			if success_callback_kwargs and any(success_callback_kwargs):
				obj.success_callback_keyword_arguments = simplejson.dumps(success_callback_kwargs)
		
		if failure_callback:
			if getattr(failure_callback, '__module__', ''):
				f = '%s.%s' % (failure_callback.__module__, failure_callback.__name__)
			else:
				f = callback.__name__
			
			obj.failure_callback_function = f
			
			if failure_callback_args and any(failure_callback_args):
				obj.failure_callback_arguments = simplejson.dumps(failure_callback_args)
			
			if failure_callback_kwargs and any(failure_callback_kwargs):
				obj.failure_callback_keyword_arguments = simplejson.dumps(failure_callback_kwargs)
		
		obj.save()
		return obj