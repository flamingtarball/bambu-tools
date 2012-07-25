from django.db.models import Manager, Sum
from django.conf import settings
from bambu.saas import helpers

class PlanManager(Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
	
	def matrix(self, currency = None):
		return self.get_query_set().matrix(
			currency or getattr(settings, 'CURRENCY_CODE', 'GBP')
		)