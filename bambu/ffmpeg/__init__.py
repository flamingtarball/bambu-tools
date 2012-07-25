from tempfile import mkstemp
from django.conf import settings
from django.core.files import File
from pymediainfo import MediaInfo
import os, subprocess, logging, mimetypes, time

VIDEO_ENCODING_COMMAND = 'ffmpeg -i %s -s 640x360 -vf "%sscale=iw*sar:ih , pad=max(iw\,ih*(16/9)):ow/(16/9):(ow-iw)/2:(oh-ih)/2" -aspect 16:9 -r 30000/1001 -b:v 200k -bt 240k -vcodec libx264 -vpre ipod640 -acodec libfaac -ac 2 -ar 48000 -ab 192k -y %s'
# VIDEO_ENCODING_COMMAND = 'ffmpeg -i %s -s 640x360 -vf "%sscale=iw*sar:ih , pad=max(iw\,ih*(16/9)):ow/(16/9):(ow-iw)/2:(oh-ih)/2" -aspect 16:9 -r 30000/1001 -b:v 200k -bt 240k -ac 2 -ar 48000 -ab 192k -strict experimental -y %s'
THUMBNAIL_ENCODING_COMMAND = 'ffmpeg -i %s -vf "scale=iw*sar:ih , pad=max(iw\,ih*(16/9)):ow/(16/9):(ow-iw)/2:(oh-ih)/2" -aspect 16:9 -f image2 -vframes 1 -y %s'

def _run_command(command, extension, source, callback = None, *callback_args, **callback_kwargs):
	handles = []
	logger = logging.getLogger('bambu.ffmpeg')
	logging.info('Started encode')
	cleanup = [source]
	transpose = ''
	
	info = MediaInfo.parse(source)
	video_tracks = [t for t in info.tracks if t.track_type == 'Video']
	
	for video in video_tracks:
		if video.rotation == '90.000':
			transpose = 'transpose=1,'
		elif video.rotation == '180.000':
			transpose = 'vflip,'
		elif video.rotation == '270.000':
			transpose = 'transpose=2,'
	
	try:
		handle, dest = mkstemp(
			extension,
			dir = settings.TEMP_DIR
		)
		
		os.close(handle)
		
		if callback:
			cleanup.append(dest)
		
		output = subprocess.Popen(
			command % (source, transpose, dest),
			shell = True,
			stdout = subprocess.PIPE
		).stdout.read()
		
		if os.stat(dest).st_size > 0:
			f = open(dest, 'r')
			handles.append(f)
			success = True
		else:
			success = False
		
		d = {
			'command': command % (source, transpose, dest),
			'source': source,
			'dest': dest,
			'extension': extension,
			'output': output
		}
		
		if success:
			logger.info('Conversion successful',
				extra = {
					'data': d
				}
			)
			
			if callback:
				callback(dest, *callback_args, **callback_kwargs)
			else:
				return dest
		else:
			logger.error('Conversion failed',
				extra = {
					'data': d
				}
			)
			
			if callback:
				callback(None, *callback_args, **callback_kwargs)
	except Exception, ex:
		logger.error('Error encoding: %s' % unicode(ex))
	finally:
		for f in cleanup:
			if os.path.exists(f):
				os.remove(f)
		
		for f in handles:
			f.close()

def convert_video(source, callback = None, *callback_args, **callback_kwargs):
	if 'bambu.tasks' in settings.INSTALLED_APPS:
		from bambu import tasks
		
		if isinstance(source, File):
			handle, source_name = mkstemp(
				'.mp4',
				dir = settings.TEMP_DIR
			)

			os.write(handle, source.read())
			os.close(handle)
			source = source_name
		
		tasks.run(
			_run_command,
			source = source,
			command = VIDEO_ENCODING_COMMAND,
			extension = '.mp4',
			success_callback = callback,
			success_callback_args = callback_args,
			success_callback_kwargs = callback_kwargs,
			failure_callback = callback,
			failure_callback_args = callback_args,
			failure_callback_kwargs = callback_kwargs,
		)
	else:
		_run_command(VIDEO_ENCODING_COMMAND, '.mp4', source, callback, *callback_args, **callback_kwargs)

def create_thumbnail(source, callback, *callback_args, **callback_kwargs):
	if 'bambu.tasks' in settings.INSTALLED_APPS:
		from bambu import tasks
		
		if isinstance(source, File):
			handle, source_name = mkstemp(
				'.jpg',
				dir = settings.TEMP_DIR
			)

			os.write(handle, source.read())
			os.close(handle)
			source = source_name
		
		tasks.run(
			_run_command,
			source = source,
			command = THUMBNAIL_ENCODING_COMMAND,
			extension = '.jpg',
			success_callback = callback,
			success_callback_args = callback_args,
			success_callback_kwargs = callback_kwargs,
			failure_callback = callback,
			failure_callback_args = callback_args,
			failure_callback_kwargs = callback_kwargs,
		)
	else:
		_run_command(THUMBNAIL_ENCODING_COMMAND, '.jpg', source, callback, *callback_args, **callback_kwargs)