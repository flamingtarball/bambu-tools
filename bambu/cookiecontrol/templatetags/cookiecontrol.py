SCRIPT = """{% load markup %}<script src="http://www.geoplugin.net/javascript.gp"></script>
<script src="{{ STATIC_URL }}cookiecontrol/js/cookiecontrol.js"></script>
<script>//<![CDATA[
	cookieControl(
		{
			introText: '{{ intro_text|markdown|escapejs }}',
			fullText: '{{ full_text|markdown|escapejs }}',
			position: '{{ position|escapejs }}',
			shape: '{{ shape|escapejs }}',
			theme: '{{ theme|escapejs }}',
			startOpen: true,
			autoHide: {{ timeout }},
			subdomains: true,
			onAccept: function() {},
			onReady: function() {},
			onCookiesAllowed: function() {},
			onCookiesNotAllowed: function() {},
			countries: {% if countries %}['{{ countries|join:"', '" }}']{% else %}''{% endif %}
		}
	);
	
	document.write('<style>.ccc-inner h2 { line-height: inherit; }</style>');
//]]></script>"""

INTRO_TEXT = 'This site uses some unobtrusive cookies to store information on your computer.'
FULL_TEXT = """Some cookies on this site are essential, and the site won't work as expected without
them. These cookies are set when you submit a form, login or interact with the site by doing
something that goes beyond clicking on simple links.

We also use some non-essential cookies to anonymously track visitors or enhance your experience of
the site. If you're not happy with this, we won't set these cookies but some nice features of the
site may be unavailable."""

POSITION = 'left'
SHAPE = 'triangle'
THEME = 'dark'
COUNTRIES = ''
TIMEOUT = 6

from django.template import Library, Template, Context
from django.conf import settings
from django.core.cache import cache
register = Library()

@register.simple_tag()
def cookiecontrol_js():
	if not cache.get('bambu.cookiecontrol'):
		ccsettings = {
			'INTRO_TEXT': INTRO_TEXT,
			'FULL_TEXT': FULL_TEXT,
			'POSITION': POSITION,
			'SHAPE': SHAPE,
			'THEME': THEME,
			'COUNTRIES': COUNTRIES,
			'TIMEOUT': TIMEOUT
		}
	
		ccsettings.update(
			getattr(settings, 'COOKIECONTROL_OPTIONS', {})
		)
		
		cache.set('bambu.cookiecontrol',
			Template(SCRIPT).render(
				Context(
					{
						'STATIC_URL': settings.STATIC_URL,
						'intro_text': ccsettings['INTRO_TEXT'],
						'full_text' : ccsettings['FULL_TEXT'],
						'position': ccsettings['POSITION'],
						'shape': ccsettings['SHAPE'],
						'theme': ccsettings['THEME'],
						'countries': ccsettings['COUNTRIES'],
						'timeout': ccsettings['TIMEOUT'] * 1000
					}
				)
			)
		)
	
	return cache.get('bambu.cookiecontrol')