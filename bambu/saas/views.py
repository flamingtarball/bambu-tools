from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils import simplejson
from django.utils.translation import ugettext as _
from bambu.saas.models import *
from bambu.saas.helpers import get_currency_symbol, format_price, fix_discount_code
from bambu.saas.forms import SignupForm, PasswordResetForm, ProfileForm
from bambu.payments.models import TaxRate
from urllib import urlencode

def plans(request):
	return TemplateResponse(
		request,
		'saas/plans.html',
		{
			'matrix': Plan.objects.matrix(),
			'menu_selection': 'plans'
		}
	)

@login_required
def upgrade(request):
	feature = request.GET.get('feature')
	plan = get_object_or_404(UserPlan, user = request.user).plan
	value = None
	
	if feature:
		try:
			feature = plan.features.get(feature__slug = feature)
			value = feature.value
		except PlanFeature.DoesNotExist:
			feature = None
	
	return TemplateResponse(
		request,
		'saas/upgrade.html',
		{
			'feature': feature,
			'value': value,
			'plan': plan,
			'menu_selection': 'profile',
			'matrix': Plan.objects.exclude(
				pk = plan.pk
			).filter(
				order__gte = plan.order
			).matrix()
		}
	)

def signup(request):
	if request.user.is_authenticated():
		messages.warning(request, u'You already have an account.')
		
		return HttpResponseRedirect(
			getattr(settings, 'LOGIN_REDIRECT_URL', '/')
		)
		
	plan = get_object_or_404(Plan,
		pk = request.GET.get('plan') or settings.SAAS_DEFAULT_PLAN
	)
	
	if request.GET.get('discount'):
		code = fix_discount_code(request.GET.get('discount', ''))
		if not code and request.method == 'GET':
			messages.warning(request, '%s is not a valid discount code' % request.GET['discount'])
	else:
		code = ''
	
	form = SignupForm(
		data = request.POST or None,
		initial = {
			'plan': plan.pk,
			'discount_code': code
		}
	)
	
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user)
		request.session['PAYMENT_GATEWAY'] = form.cleaned_data['payment_gateway']
		
		return HttpResponseRedirect(
			reverse('signup_pay')
		)
	
	currency = getattr(settings, 'DEFAULT_CURRENCY', 'GBP')
	symbol = get_currency_symbol(currency)
	
	tax_rate = TaxRate.objects.get(
		chargeable_percent = settings.PAYMENTS_DEFAULT_TAXRATE
	)
	
	prices = {}
	for p in Plan.objects.all():
		try:
			price = p.prices.get(currency = currency)
			price_monthly = format_price(symbol, price.monthly)
			price_yearly = format_price(symbol, price.yearly)
		except Price.DoesNotExist:
			price_monthly = format_price(symbol, 0)
			price_yearly = format_price(symbol, 0)
		
		prices[p.pk] = (
			(1, _(u'Monthly (%s + %s)' % (price_monthly, tax_rate.shorthand))),
			(12, _(u'Annually (%s + %s)' % (price_yearly, tax_rate.shorthand)))
		)
	
	return TemplateResponse(
		request,
		'saas/signup.html',
		{
			'form': form,
			'selected_plan': plan,
			'next': request.GET.get('next'),
			'matrix': Plan.objects.matrix(),
			'plan_prices': simplejson.dumps(prices),
			'discount': code
		}
	)

@login_required
def signup_pay(request):
	try:
		plan = UserPlan.objects.get(user = request.user, paid = False)
	except UserPlan.DoesNotExist:
		messages.warning(request, u'You already have an account.')
		
		return HttpResponseRedirect(
			getattr(settings, 'LOGIN_REDIRECT_URL', '/')
		)
	
	gateway = request.session.get('PAYMENT_GATEWAY')
	if not gateway:
		return HttpResponse('No payment gateway provided.')
	
	currency = getattr(settings, 'DEFAULT_CURRENCY', 'GBP')
	payment = plan.create_payment(currency, gateway)
	return payment.process_view(request)

def verify_email(request, guid):
	validation = get_object_or_404(EmailValidation, guid = guid)
	validation.user.is_active = True
	validation.user.save()
	validation.delete()
	
	messages.success(request, _('Thanks for confirming your email address.'))
	
	next = getattr(settings, 'SIGNUP_REDIRECT',
		getattr(settings, 'LOGIN_REDIRECT_URL', '/')
	)
	
	return HttpResponseRedirect(
		'%s?%s' % (
			settings.LOGIN_URL,
			urlencode(
				{
					'next': next
				}
			)
		)
	)

def reset_password(request, guid = None):
	if guid:
		reset = get_object_or_404(PasswordReset, guid = guid)
		reset.reset()
		
		messages.success(request,
			_('Your new password should be in your inbox shortly.')
		)
		
		return HttpResponseRedirect(settings.LOGIN_URL)
	
	form = PasswordResetForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		try:
			user = User.objects.get(email__iexact = form.cleaned_data['email'])
			reset, created = user.password_resets.get_or_create()
		except User.DoesNotExist:
			pass
		
		return TemplateResponse(
			request,
			'saas/password-reset.html'
		)
	
	return TemplateResponse(
		request,
		'saas/forgot-password.html',
		{
			'form': form
		}
	)

@login_required
def profile(request):
	try:
		plan = UserPlan.objects.get(user = request.user)
	except UserPlan.DoesNotExist:
		plan = None
	
	return TemplateResponse(
		request,
		'saas/profile/dashboard.html',
		{
			'plan': plan,
			'breadcrumb_trail': (
				('../', u'Home'),
				('', u'My profile')
			),
			'title_parts': ('My profile',)
		}
	)

@login_required
def profile_edit(request):
	form = ProfileForm(
		data = request.POST or None,
		instance = request.user
	)
	
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		
		messages.success(request, u'Your profile has been updated.')
		
		return HttpResponseRedirect(
			reverse('profile')
		)
	
	return TemplateResponse(
		request,
		'saas/profile/edit.html',
		{
			'form': form,
			'breadcrumb_trail': (
				('../../', u'Home'),
				('../', u'My profile'),
				('', 'Edit')
			),
			'title_parts': ('Edit', 'My profile')
		}
	)