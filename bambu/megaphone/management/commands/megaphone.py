from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from bambu.megaphone.models import Feed, Item
from datetime import datetime, timedelta
from optparse import make_option

class Command(BaseCommand):
	help = 'Run tasks at scheduled intervals'
	option_list = BaseCommand.option_list + (
		make_option('--clear',
			action = 'store_true',
			dest = 'clear',
			default = False,
			help = 'Clear all items'
		),
		make_option('--force',
			action = 'store_true',
			dest = 'force',
			default = False,
			help = 'Force all feeds to be checked, even if they\'re not due for a check'
		)
	)
	
	def handle(self, *args, **options):
		if options['clear']:
			Item.objects.all().delete()
		else:
			date = datetime.utcnow().replace(tzinfo = utc)
			
			for feed in Feed.objects.filter():
				check = not feed.checked or (date - feed.checked).seconds > feed.frequency * 60
				
				if options['force'] or check:
					feed.check()