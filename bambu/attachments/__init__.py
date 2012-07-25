import re

MIMETYPES = (
	'application/x-troff-msvideo',
	'video/avi',
	'video/msvideo',
	'video/x-msvideo',
	'image/bmp',
	'image/x-windows-bmp',
	'application/msword',
	'image/gif',
	'application/x-compressed',
	'application/x-gzip',
	'multipart/x-gzip',
	'image/jpeg',
	'image/pjpeg',
	'audio/mpeg3',
	'audio/x-mpeg-3',
	'video/x-m4v',
	'video/mpeg',
	'application/pdf',
	'image/png',
	'text/plain',
	'application/excel',
	'application/vnd.ms-excel',
	'application/x-excel',
	'application/x-msexcel',
	'application/x-compressed',
	'application/x-zip-compressed',
	'application/zip',
	'multipart/x-zip'
)

ATTACHMENT_REGEX = re.compile(r'\<p\>\[attachment (\d+)\]\<\/p\>')