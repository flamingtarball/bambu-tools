from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from bambu.uploadify import signals
from bambu.uploadify.models import Upload
from tempfile import mkstemp
import os, logging

@csrf_exempt
def upload(request):
	logger = logging.getLogger('bambu.uploadify')
	
	try:
		if request.method == 'POST' and request.FILES:
			if not 'guid' in request.POST:
				return HttpResponse('')
			
			data = request.FILES['Filedata']
			data.seek(0)
			
			handle, filename = mkstemp(
				suffix = os.path.splitext(data.name)[-1],
				dir = settings.TEMP_DIR
			)
			
			os.write(handle, data.read())
			os.close(handle)
			
			Upload.objects.create(
				guid = request.POST['guid'],
				filename = filename
			)
			
			return HttpResponse('True')
		
		return HttpResponse('')
	except Exception, ex:
		logger.error(unicode(ex))