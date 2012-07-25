from django.db.models import Manager

class TokenManager(Manager):
	def create_token(self, app, token_type, timestamp, user=None):
		token, created = self.get_or_create(
			app = app, 
			token_type = token_type, 
			timestamp = timestamp,
			user = user
		)
		
		return token