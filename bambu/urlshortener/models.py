from django.db import models
from bambu.urlshortener import URL_LENGTH
import random, string

class ShortURL(models.Model):
	url = models.URLField(u'URL', max_length = 255, unique = True)
	slug = models.CharField(max_length = URL_LENGTH, unique = True, editable = False)
	visits = models.PositiveIntegerField(default = 0, editable = False)
	last_visited = models.DateTimeField(null = True, blank = True, editable = False)
	
	def __unicode__(self):
		return self.url
	
	def save(self, *args, **kwargs):
		if not self.slug:
			while True:
				self.slug = ''.join(random.sample(string.letters + string.digits, URL_LENGTH))
				if ShortURL.objects.filter(slug = self.slug).count() == 0:
					break
		
		super(ShortURL, self).save(*args, **kwargs)
	
	class Meta:
		verbose_name = 'short URL'