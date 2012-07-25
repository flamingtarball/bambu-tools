from threading import Thread
from bambu.dataportability.exceptions import InvalidFormatException

import logging

class ImportThread(Thread):
	def __init__(self, handler, data, formats, callback = None):
		Thread.__init__(self)
		self.handler = handler
		self.data = data
		self.formats = formats
		self.callback = callback
	
	def run(self):
		run_job = False
		
		try:
			if self.handler.supported_formats:
				for format in self.formats:
					if format in self.handler.supported_formats:
						run_job = True
						break
				
				if not run_job:
					raise InvalidFormatException(
						'No handlers are configured to accept this file format.'
					)
			else:
				run_job = True
			
			if run_job:
				result = self.handler._import(self.data, self.formats)
		except Exception, ex:
			self.handler.job.updates.error(
				'Error importing data',
				unicode(ex)
			)
			
			self.notify(False)
			return
		
		if self.callback:
			self.notify()
			self.callback(result)
	
	def notify(self, success = True):
		from bambu.mail import render_to_mail
		
		render_to_mail(
			'Importing %s was %s' % (
				self.handler.job.name,
				(success and 'successful' or 'not successful')
			),
			'dataportability/mail-%s.txt' % (success and 'success' or 'fail'),
			{
				'job': self.handler.job,
				'warnings': self.handler.job.updates.filter(kind = 'warning'),
				'errors': self.handler.job.updates.filter(kind = 'error')
			},
			self.handler.job.user
		)

class ExportThread(Thread):
	def __init__(self, handler, writer, callback):
		Thread.__init__(self)
		self.handler = handler
		self.writer = writer
		self.callback = callback
	
	def run(self):
		count = float(self.handler._export_count())
		
		try:
			self.writer.start()
			for i, result in enumerate(self.handler._export()):
				self.writer.item(result)
				
				self.handler.logger.debug('Progress %d' % self.handler.job.progress)
				self.handler.job.progress = int(float(i + 1) / count * 100.0)
				self.handler.job.save()
				
				self.writer.flush()
			
			self.writer.end()
		except Exception, ex:
			self.handler.job.updates.error(
				'Error exporting data',
				unicode(ex)
			)
			
			self.handler.logger.error(ex, exc_info = ex)
			return
		
		self.callback(self.writer.stream)

class HandlerBase(object):
	supported_formats = None
	export_wrapper = None
	export_item = None
	
	def __init__(self, job):
		self.job = job
		self.logger = logging.getLogger('bambu.dataportability')
	
	def start_import(self, data, formats, callback):
		thread = ImportThread(self, data, formats, callback)
		thread.start()
	
	def start_export(self, writer, callback):
		thread = ExportThread(self, writer, callback)
		thread.start()
	
	def _import(self, data, formats):
		raise NotImplementedError('Method not implemented.')
	
	def _export_count(self):
		return 0
	
	def _export(self):
		raise NotImplementedError('Method not implemented.')