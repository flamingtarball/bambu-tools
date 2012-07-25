from django.template import Library
from django.conf import settings

register = Library()

@register.inclusion_tag('analytics/google.inc.html', takes_context = True)
def google_analytics(context, track_pageview = 'yes'):
	request = context.get('request')
	
	if request:
		if request.user.is_authenticated() and request.user.is_staff:
			return {}
		
		return {
			'ids': getattr(settings, 'GOOGLE_ANALYTICS_IDS', ()),
			'track_pageview': track_pageview != 'no',
			'queue': context.get('_gaq')
		}
	
	return {'ids': []}

@register.inclusion_tag('analytics/adwords.inc.html', takes_context = True)
def adwords_conversion(context, campaign, amount = 0, label = None):
	try:
		con = settings.ADWORDS_CAMPAIGNS.get(campaign)
	except KeyError:
		return {}
	
	request = context.get('request')
	
	try:
		conversion_id, label, amount = con
	except:
		try:
			conversion_id, label = con
		except:
			conversion_id = con
			if isinstance(conversion_id, (list, tuple)):
				conversion_id = conversion_id[0]
	
	return {
		'conversion': conversion_id,
		'amount': amount,
		'label': label,
		'request': request
	}

@register.simple_tag(takes_context = True)
def track_event(context, category, action, label = '', value = 0, noninteractive = False):
	request = context.get('request')
	
	if request:
		if request.user.is_authenticated() and request.user.is_staff:
			return ''
	
	queue = context.get('_gaq', [])
	queue.append(
		(
			'_trackEvent',
			[
				"'%s'" % category,
				"'%s'" % action,
				"'%s'" % label,
				value,
				noninteractive and 'true' or 'false'
			]
		)
	)
	
	context['_gaq'] = queue
	return ''