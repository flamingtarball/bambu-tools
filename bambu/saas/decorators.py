from django.http import HttpResponseRedirect
from bambu.saas.models import UserPlan, Feature
from bambu.saas.helpers import test_feature
from django.core.urlresolvers import reverse
from urllib import urlencode

def feature_required(feature, redirect_url = '/upgrade/', **kw):
	def _dec(view_func):
		def _view(request, *args, **kwargs):
			if request.user.is_authenticated():
				try:
					plan = UserPlan.objects.get(user = request.user)
					
					for k, v in kw.items():
						if callable(v):
							kw[k] = v(*args, **kwargs)
					
					try:
						feat = plan.plan.features.get(feature__slug = feature)
						if (feat.feature.is_boolean and feat.value) or feat.value == -1:
							return view_func(request, *args, **kwargs)
						else:
							if test_feature(feat.feature, request.user, feat.value, **kw):
								return view_func(request, *args, **kwargs)
					except Feature.DoesNotExist:
						pass
				except UserPlan.DoesNotExist:
					pass
			
				return HttpResponseRedirect('%s?feature=%s' % (redirect_url, feature))
			
			return HttpResponseRedirect(
				'%s?%s' % (
					reverse('signup'),
					urlencode(
						{
							'next': request.path
						}
					)
				)
			)
		
		return _view
	
	return _dec