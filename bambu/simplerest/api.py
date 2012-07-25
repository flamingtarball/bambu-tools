from urllib2 import Request, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, HTTPError
from urllib2 import urlopen, build_opener, install_opener
from urllib import urlencode
from bambu.simplerest.poster.encode import multipart_encode
from bambu.simplerest.poster.streaminghttp import register_openers
import simplejson

FORMAT = 'json'

class API(object):
	def __init__(self, domain, base = 'api', **kwargs):
		self.__base = base
		
		if not 'parent' in kwargs:
			self.__domain = domain
			
			if 'username' in kwargs and 'password' in kwargs:
				manager = HTTPPasswordMgrWithDefaultRealm()
				manager.add_password(None,
					'http://%s/' % self.__domain, kwargs['username'], kwargs['password']
				)
			elif 'token' in kwargs and 'secret' in kwargs:
				self.__token = token
				self.__secret = secret
			opener = register_openers()
			opener.add_handler(HTTPBasicAuthHandler(manager))
			install_opener(opener)
		else:
			self.__parent = kwargs['parent']
			self.__domain = self.__parent.__domain
			
			if hasattr(self.__parent, '__token') and hasattr(self.__parent, '__secret'):
				self.__token = self.__parent.__token
				self.__secret = self.__parent.__secret
	
	def __getattr__(self, name):
		if not hasattr(self, name):
			api = API(self.__domain, base = self.__base + '/' + name, parent = self)
			object.__setattr__(self, name, api)
			return api
		
		return object.__getattribute__(self, name)
	
	def __do(self, url, method, data = {}, qsargs = {}):
		data, headers = multipart_encode(data)
		
		if any(qsargs):
			qs = '?' + urlencode(qsargs)
		else:
			qs = ''
		
		request = Request(
			'http://%s/%s%s.%s%s' % (
				self.__domain, self.__base, url, FORMAT, qs
			), data, headers
		)
		
		request.get_method = lambda: method
		
		try:
			data = simplejson.loads(
				urlopen(request).read()
			)
			
			if isinstance(data, dict):
				return Result(self, self.__domain, self.__base, **data)
			elif isinstance(data, list):
				is_result = False
				items = []
				
				for d in data:
					if isinstance(d, dict):
						is_result = True
						items.append(Result(self, self.__domain, self.__base, **d))
					elif is_result:
						return data
					else:
						items.append(items)
				
				return items
			else:
				return data
		except HTTPError, ex:
			data = ex.read()
			raise Exception(simplejson.loads(data))
	
	def read(self, id = None, **kwargs):
		url = id and ('/%d' % id) or ''
		return self.__do(url, 'GET', qsargs = kwargs)
	
	def update(self, id, **kwargs):
		return self.__do('/%d' % int(id), 'PUT', kwargs)
	
	def get(self, namespace):
		return self.__do('/%s' % namespace, 'GET')
	
	def post(self, namespace, **kwargs):
		return self.__do('/%s' % namespace, 'POST', kwargs)
	
	def create(self, **kwargs):
		return self.__do('', 'POST', kwargs)
	
	def delete(self, id):
		result = self.__do('/%d' % int(id), 'DELETE')
		return 'OK' in result

class Result(object):
	__values = []
	
	def __init__(self, api, domain, base, *args, **kwargs):
		for arg in args:
			self.__values.append(arg)
		
		for key, value in kwargs.items():
			if isinstance(value, dict):
				setattr(self, key, Result(api, domain, base, **value))
			elif isinstance(value, list):
				items = []
				for item in value:
					if isinstance(item, dict):
						items.append(Result(api, domain, base, **item))
					else:
						items.append(item)
				
				setattr(self, key, items)
			else:
				setattr(self, key, value)
		
		self.__api = api
		self.__domain = domain
		self.__base = base
	
	def __getitem__(self, index):
		return self.__values[index]
	
	def __getattr__(self, name):
		if not hasattr(self, name):
			api = API(self.__domain, parent = self.__api,
				base = '%s/%d/%s' % (self.__base, int(self.id), name)
			)
			
			object.__setattr__(self, name, api)
			return api
		
		return object.__getattribute__(self, name)
	
	def update(self, **kwargs):
		return self.__api.update(self.id, **kwargs)
	
	def delete(self):
		return self.__api.delete(self.id)