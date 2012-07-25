from bambu.activity import _thread_locals

class RequestMiddleware(object):
	def process_request(self, request):
		_thread_locals.request = request