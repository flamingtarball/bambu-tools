from django.db.models import Manager

class StreamManager(Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
	
	def get_for_user(self, user):
		return self.get_query_set().get_for_user(user)