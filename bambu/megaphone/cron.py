from bambu import cron
from bambu.megaphone.models import Feed, Item, Place
from datetime import datetime, timedelta
from django.utils.timezone import utc

class FeedJob(cron.CronJob):
	frequency = cron.MINUTE
	
	def run(self, logger):
		date = datetime.utcnow().replace(tzinfo = utc)
		
		for feed in Feed.objects.all():
			if not feed.checked or (date - feed.checked).seconds > feed.frequency * 60:
				feed.check()

cron.site.register(FeedJob)