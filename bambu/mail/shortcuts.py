import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings

def render_to_mail(subject, template, context, recipient, fail_silently = False):
	from_email = getattr(settings, 'DEFAULT_FROM_EMAIL')
	site = Site.objects.get_current()
	
	if isinstance(recipient, User):
		recipients = [recipient.email]
	elif isinstance(recipient, (str, unicode)):
		recipients = [recipient]
	elif isinstance(recipient, (list, tuple)):
		recipients = recipient
	else:
		raise Exception('recipient argument must be User, string, list or tuple')
	
	ctx = {
		'MEDIA_URL': settings.MEDIA_URL,
		'STATIC_URL': settings.STATIC_URL,
		'SITE': site,
		'template': template
	}
	
	if ctx['MEDIA_URL'].startswith('/'):
		ctx['MEDIA_URL'] = 'http://%s%s' % (ctx['SITE'].domain, ctx['MEDIA_URL'])
	
	ctx.update(context)
	
	email = EmailMultiAlternatives(
		subject,
		render_to_string('mail/base.txt', ctx),
		from_email, recipients
	)
	
	email.attach_alternative(
		render_to_string('mail/base.html', ctx),
		"text/html"
	)
	
	logger = logging.getLogger()
	
	try:
		email.send()
		logger.info('Sent email to %s from %s' % (', '.join(recipients), from_email))
	except:
		if not fail_silently:
			raise