from django.db.models import Model
from collections import Iterable
from bambu.api.transformers import library

class Serialiser(object):
	def __init__(self, max_detail_level = 1):
		self.max_detail_level = max_detail_level
	
	def serialise(self, data):
		raise NotImplementedError('Not implemented.')
	
	def _prepare(self, data):
		if data:
			if isinstance(data, Iterable):
				if not isinstance(data, dict):
					return [
						self._make_dict(v) for v in data
					]
			else:
				return self._make_dict(data)
		else:
			return []
	
	def _make_dict(self, obj, level = 1):
		if isinstance(obj, Model):
			return library.transform(obj, self.max_detail_level)
		
		return unicode(obj)

class JSONSerialiser(Serialiser):
	def serialise(self, data):
		from django.utils import simplejson
		
		return simplejson.dumps(
			self._prepare(data)
		)

class XMLSerialiser(Serialiser):
	def _write(self, writer, key, data):
		if isinstance(data, dict):
			writer.start(key)
			for (subkey, subdata) in data.items():
				self._write(writer, subkey, subdata)
			writer.end(key)
		elif isinstance(data, list):
			for subdata in data:
				self._write(writer, key, subdata)
		elif data:
			writer.element(key, unicode(data))
	
	def serialise(self, data):
		from bambu.api.xml import XMLWriter
		from StringIO import StringIO
		
		data = self._prepare(data)
		string = StringIO()
		writer = XMLWriter(string)
		
		if isinstance(data, dict):
			writer.start('result')
			for (key, subdata) in data.items():
				self._write(writer, key, subdata)
			writer.end('result')
		elif isinstance(data, (list, tuple)):
			writer.start('results')
			for d in data:
				self._write(writer, 'result', d)
			writer.end('results')
		elif isinstance(data, Iterable) and not isinstance(data, (str, unicode)):
			writer.start('results')
			for d in data:
				if isinstance(d, dict):
					writer.start('result')
					for (subkey, subdata) in d.items():
						if subdata:
							self._write(writer, subkey, subdata)
					writer.end('result')
				else:
					writer.element('result', d)
			
			writer.end('results')
		elif data:
			writer.element('result', unicode(data))
		
		string.seek(0)
		return string.read()