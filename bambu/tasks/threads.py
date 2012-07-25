from django.conf import settings
from django.utils.timezone import utc
from threading import Thread
from bambu.tasks import TASK_QUEUED, TASK_PROCESSING, TASK_COMPLETE, TASK_FAILED, \
	MAX_CONCURRENT_TASKS
from datetime import datetime
import logging

class TaskThread(Thread):
	def __init__(self, id, func, args, kwargs):
		Thread.__init__(self)
		
		self.id = id
		self.func = func
		self.args = args
		self.kwargs = kwargs
		self.logger = logging.getLogger('bambu.tasks')
	
	def run(self):
		from bambu.tasks.models import Task
		
		self.logger.info('Task %d started' % self.id)
		
		task = Task.objects.get(pk = self.id)
		task.state = TASK_PROCESSING
		task.updated = datetime.utcnow().replace(tzinfo = utc)
		task.save()
		
		try:
			value = self.func(*self.args, **self.kwargs)
			task = Task.objects.get(pk = self.id)
			task.state = TASK_COMPLETE
			
			self.logger.info('Task %d completed' % task.pk)
			task.callback(True, value)
		except Exception, ex:
			task = Task.objects.get(pk = self.id)
			task.state = TASK_FAILED
			task.updated = datetime.utcnow().replace(tzinfo = utc)
			
			self.logger.error(
				'Task %d failed: %s' % (
					self.id,
					unicode(ex)
				)
			)
			
			task.callback(False)
		
		task.updated = datetime.utcnow().replace(tzinfo = utc)
		task.save()
		
		running = Task.objects.exclude(pk = self.id).filter(state = TASK_PROCESSING).count()
		free_slots = MAX_CONCURRENT_TASKS - running
		
		if free_slots > 0:
			self.logger.info('%d free slot(s). Ready for a new task' % free_slots)
			for task in Task.objects.filter(state = TASK_QUEUED)[:free_slots]:
				task.start()