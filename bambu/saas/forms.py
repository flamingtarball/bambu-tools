# encoding: utf-8

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from bambu.saas.models import Plan, UserPlan, Discount
from bambu.saas.helpers import get_currency_symbol, format_price
from bambu.saas.fields import ImageChoiceField
from bambu.payments import get_gateway_choices
from bambu.payments.models import TaxRate

class SignupForm(forms.Form):
	first_name = forms.CharField(max_length = 20)
	last_name = forms.CharField(max_length = 20)
	email = forms.EmailField(label = _('Email address'))
	
	username = forms.RegexField(
		label = _('Username'), max_length = 30, regex = r'^[\w.@+-]+$',
		help_text = _('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'),
		error_messages = {
			'invalid': _('This value may contain only letters, numbers and @/./+/-/_ characters.')
		}
	)
	
	password1 = forms.CharField(label = _('Password'), widget = forms.PasswordInput)
	password2 = forms.CharField(label = _('Confirm password'), widget = forms.PasswordInput,
		help_text = _('Enter the same password as above, for verification.')
	)
	
	plan = forms.ModelChoiceField(queryset = Plan.objects, empty_label = None)
	period = forms.ChoiceField(
		label = _(u'Billing frequency'),
		choices = (
			(1, _('Monthly')),
			(12, _('Annually'))
		),
		initial = 12
	)
	
	payment_gateway = ImageChoiceField(
		label = _('Pay via'), choices = get_gateway_choices(True, False)
	)
	
	discount_code = forms.CharField(
		max_length = 50, required = False,
		help_text = u'If you have a discount code, enter it here.'
	)
	
	def __init__(self, *args, **kwargs):
		currency = kwargs.pop('currency',
			getattr(settings, 'DEFAULT_CURRENCY', 'GBP')
		)
		
		super(SignupForm, self).__init__(*args, **kwargs)
		
		if Plan.objects.count() == 1:
			plan = Plan.objects.get(pk = settings.SAAS_DEFAULT_PLAN)
			del self.fields['plan']
		else:
			plan = Plan.objects.get(
				pk = self.initial.get('plan') or settings.SAAS_DEFAULT_PLAN
			)
		
		tax_rate = TaxRate.objects.get(
			chargeable_percent = settings.PAYMENTS_DEFAULT_TAXRATE
		)
		
		symbol = get_currency_symbol(currency)
		price = plan.prices.get(currency = currency)
		price_monthly = format_price(symbol, price.monthly)
		price_yearly = format_price(symbol, price.yearly)
		
		self.fields['period'].choices = (
			(1, _('Monthly (%s + %s)' % (price_monthly, tax_rate.shorthand))),
			(12, _('Annually (%s + %s)' % (price_yearly, tax_rate.shorthand)))
		)
		
		self.free = price.monthly == 0 and price.yearly == 0
	
	def clean_username(self):
		username = self.cleaned_data['username']
		
		try:
			User.objects.get(username__iexact = username)
		except User.DoesNotExist:
			return username.lower()
		
		raise forms.ValidationError(
			_('A user with that username already exists.')
		)
	
	def clean_password2(self):
		password1 = self.cleaned_data.get('password1', '')
		password2 = self.cleaned_data['password2']
		
		if password1 != password2:
			raise forms.ValidationError(
				_('The two password fields don\'t match.')
			)
		
		return password2
	
	def clean_email(self):
		email = self.cleaned_data['email']

		try:
			User.objects.get(email__iexact = email)
		except User.DoesNotExist:
			return email
		
		raise forms.ValidationError(
			_('A user with that email address already exists.')
		)
	
	def clean_discount_count(self):
		code = self.cleaned_data.get('discount_code')
		
		if code:
			try:
				discount = Discount.objects.get(code__iexact = code)
				return discount.code
			except Discount.DoesNotExist:
				raise forms.ValidationError('No discount found for that code.')
		
		return ''
	
	def clean(self):
		period = self.cleaned_data.get('period')
		code = self.cleaned_data.get('discount_code')
		
		if code:
			try:
				discount = Discount.objects.get(code__iexact = code)
				if not discount.valid_yearly and int(period) == 12:
					raise forms.ValidationError(
						u'This discount code is not available for annual subscriptions.'
					)
			except Discount.DoesNotExist:
				pass
		
		return self.cleaned_data
	
	def save(self, commit = True):
		user = User.objects.create_user(
			username = self.cleaned_data['username'],
			password = self.cleaned_data['password1'],
			email = self.cleaned_data['email']
		)
		
		user.first_name = self.cleaned_data['first_name']
		user.last_name = self.cleaned_data['last_name']
		user.save()
		
		if self.free:
			# Because the user's paying, we don't really need to validate
			# their email address.
			user.email_validations.create()
		
		plan = self.cleaned_data.get('plan',
			Plan.objects.get(pk = settings.SAAS_DEFAULT_PLAN),
		)
		
		if self.cleaned_data.get('discount_code'):
			discount = Discount.objects.get(
				code__iexact = self.cleaned_data['discount_code']
			)
		else:
			discount = None
		
		UserPlan.objects.create(
			user = user, plan = plan,
			period = int(self.cleaned_data['period']),
			discount = discount
		)
		
		return authenticate(
			username = self.cleaned_data['username'],
			password = self.cleaned_data['password1']
		)

class PasswordResetForm(forms.Form):
	email = forms.EmailField(label = _('Email address'))

class ProfileForm(forms.ModelForm):
	first_name = forms.CharField(max_length = 20)
	last_name = forms.CharField(max_length = 20)
	email = forms.EmailField(label = _('Email address'))
	
	password1 = forms.CharField(
		label = _('Change password'), widget = forms.PasswordInput,
		required = False
	)
	
	password2 = forms.CharField(
		label = _('Confirm password'), widget = forms.PasswordInput,
		help_text = _('Enter the same password as above, for verification.'),
		required = False
	)
	
	def clean_password2(self):
		password1 = self.cleaned_data.get('password1', '')
		password2 = self.cleaned_data.get('password2', '')
		
		if password1 != password2:
			raise forms.ValidationError(
				_('The two password fields don\'t match.')
			)

		return password2
	
	def clean_email(self):
		email = self.cleaned_data['email']
		
		try:
			User.objects.exclude(pk = self.instance.pk).get(email__iexact = email)
		except User.DoesNotExist:
			return email
		
		raise forms.ValidationError(
			_('A user with that email address already exists.')
		)
	
	def save(self, commit = True):
		user = super(ProfileForm, self).save(commit = False)
		
		if self.cleaned_data.get('password1'):
			user.set_password(self.cleaned_data['password1'])
		
		if commit:
			user.save()
		
		return user
		
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email')