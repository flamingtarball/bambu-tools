from django.conf import settings
import logging

TASK_QUEUED = 0
TASK_PROCESSING = 1
TASK_COMPLETE = 2
TASK_FAILED = -1
TASK_CANCELLED = -2

MAX_CONCURRENT_TASKS = getattr(settings, 'MAX_CONCURRENT_TASKS', 3)
TASK_LIFESPAN = getattr(settings, 'TASK_LIFESPAN', 30)

def run(func,
	success_callback = None, success_callback_args = None, success_callback_kwargs = None,
	failure_callback = None, failure_callback_args = None, failure_callback_kwargs = None,
	*args, **kwargs
):
	from bambu.tasks.models import Task
	
	logger = logging.getLogger('bambu.tasks')
	task = Task.objects.create_task(func,
		success_callback = success_callback,
		success_callback_args = success_callback_args,
		success_callback_kwargs = success_callback_kwargs,
		failure_callback = failure_callback,
		failure_callback_args = failure_callback_args,
		failure_callback_kwargs = failure_callback_kwargs,
		*args, **kwargs
	)
	
	running = Task.objects.filter(state = TASK_PROCESSING).count()
	free_slots = MAX_CONCURRENT_TASKS - running
	
	if free_slots > 0:
		logger.info('%d free slot(s). Running task immediately' % free_slots)
		task.start()

def schedule(func, date,
	success_callback = None, success_callback_args = None, success_callback_kwargs = None,
	failure_callback = None, failure_callback_args = None, failure_callback_kwargs = None,
	*args, **kwargs
):
	from bambu.tasks.models import Task
	
	Task.objects.create_task(func,
		date = date,
		success_callback = success_callback,
		success_callback_args = success_callback_args,
		success_callback_kwargs = success_callback_kwargs,
		failure_callback = failure_callback,
		failure_callback_args = failure_callback_args,
		failure_callback_kwargs = failure_callback_kwargs,
		*args, **kwargs
	)