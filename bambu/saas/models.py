from django.db import models
from django.conf import settings
from django.utils.datastructures import SortedDict
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils.timezone import utc
from bambu.saas import helpers
from bambu.saas.managers import PlanManager
from bambu.mail.shortcuts import render_to_mail
from bambu.payments.models import Payment, TaxRate
from bambu.payments.signals import *
from datetime import datetime, timedelta
from uuid import uuid4
import logging

class Plan(models.Model):
	name = models.CharField(max_length = 50)
	description = models.TextField(null = True, blank = True)
	best_value = models.BooleanField()
	order = models.PositiveIntegerField(default = 1)
	trial_months = models.PositiveIntegerField('trial period', default = 0,
		help_text = u'Number of months worth of free trial'
	)
	
	objects = PlanManager()
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('order',)
	
	class QuerySet(models.query.QuerySet):
		def matrix(self, currency = None):
			headings = []
			features = SortedDict()
			currency = currency or getattr(settings, 'CURRENCY_CODE', 'GBP')
			
			for feature in Feature.objects.all():
				features[feature.slug] = (
					feature.name,
					feature.is_boolean,
					feature.description
				)
			
			rows = [
				{
					'heading': n,
					'columns': [],
					'slug': k,
					'boolean': b,
					'description': d or ''
				} for (k, (n, b, d)) in features.items()
			]
			
			symbol = helpers.get_currency_symbol(currency)
			for plan in self.all():
				try:
					price = plan.prices.get(currency = currency)
				except Price.DoesNotExist:
					try:
						price = plan.prices.get(
							currency = getattr(settings, 'CURRENCY_CODE', 'GBP')
						)
					except Price.DoesNotExist:
						price = None
				
				h = {
					'name': plan.name,
					'pk': plan.pk
				}
				
				if plan.best_value:
					h['best'] = True
				
				if price:
					h.update(
						{
							'price_monthly': price and helpers.format_price(
								symbol, price.monthly
							) or None,
							'price_yearly': price and helpers.format_price(
								symbol, price.yearly
							) or None
						}
					)
				
				headings.append(h)
				
				for row in rows:
					try:
						feature = plan.features.get(feature__slug = row['slug'])
						row['columns'].append(
							{
								'best': plan.best_value,
								'value': feature.value
							}
						)
					except:
						row['columns'].append(
							{
								'best': plan.best_value,
								'value': 0
							}
						)
			
			return {
				'headings': headings,
				'rows': rows
			}
	
class Price(models.Model):
	plan = models.ForeignKey(Plan, related_name = 'prices')
	monthly = models.DecimalField(decimal_places = 2, max_digits = 6)
	yearly = models.DecimalField(decimal_places = 2, max_digits = 8)
	currency = models.CharField(max_length = 3, choices = helpers.get_currencies(),
		default = getattr(settings, 'CURRENCY_CODE', 'GBP')
	)
	
	def get_currency_symbol(self):
		return helpers.get_currency_symbol(self.currency)
	
	def __unicode__(self):
		return u'%s%s per month' % (self.get_currency_symbol(), self.monthly)
	
	class Meta:
		ordering = ('monthly',)
		unique_together = ('plan', 'currency')
		
class Feature(models.Model):
	name = models.CharField(max_length = 50)
	slug = models.SlugField(max_length = 50, unique = True)
	is_boolean = models.BooleanField()
	order = models.PositiveIntegerField(default = 1)
	description = models.TextField(null = True, blank = True)
	test_function = models.CharField(max_length = 255, null = True, blank = True)
	upgrade_cta = models.CharField(u'upgrade call-to-action',
		max_length = 255, null = True, blank = True
	)
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('order',)

class PlanFeature(models.Model):
	plan = models.ForeignKey(Plan, related_name = 'features')
	feature = models.ForeignKey(Feature, related_name = 'plans')
	value = models.IntegerField(default = 0, help_text = u'Use -1 for unlimited')
	groups = models.ManyToManyField('auth.Group', related_name = 'groups',
		null = True, blank = True,
		help_text = u'Select the groups that provide permissions for this feature'
	)
	
	def __unicode__(self):
		return u'%s (%s)' % (
			self.feature,
			self.feature.is_boolean and (self.value == 1 and 'Yes' or 'No') or self.value
		)
	
	class Meta:
		unique_together = ('plan', 'feature')

class Discount(models.Model):
	name = models.CharField(max_length = 50)
	description = models.TextField(null = True, blank = True)
	percent = models.FloatField()
	months = models.PositiveIntegerField(
		default = 1,
		help_text = u'The number of months the discount applies for'
	)
	
	code = models.CharField(max_length = 50, unique = True)
	valid_yearly = models.BooleanField(default = True)
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('-percent',)

class UserPlan(models.Model):
	plan = models.ForeignKey(Plan, related_name = 'users')
	user = models.ForeignKey(User, related_name = 'plans', unique = True)
	started = models.DateField()
	paid_start = models.DateField()
	expiry = models.DateField(null = True, blank = True)
	renewed = models.DateField(null = True, blank = True)
	period = models.PositiveIntegerField(
		choices = (
			(1, u'One month'),
			(12, u'One year')
		), default = 12
	)
	
	paid = models.BooleanField()
	discount = models.ForeignKey('saas.Discount', related_name = 'user_plans',
		null = True, blank = True
	)
	
	def __unicode__(self):
		return unicode(self.plan)
	
	def save(self, *args, **kwargs):
		if not self.started:
			now = datetime.utcnow().date().replace(tzinfo = utc)
			self.started = now
			
			day = now.day
			month = now.month + self.plan.trial_months
			year = now.year
			
			while month > 12:
				year += 1
				month -= 12
			
			self.paid_start = (
				datetime(year, month, day, 0, 0, 0) - timedelta(days = 1)
			).replace(tzinfo = utc)
			
			day = self.paid_start.day
			month = self.paid_start.month + self.period
			year = self.paid_start.year
			
			while month > 12:
				year += 1
				month -= 12
			
			self.expiry = (
				datetime(year, month, day, 0, 0, 0) - timedelta(days = 1)
			).replace(tzinfo = utc)
		
		super(UserPlan, self).save(*args, **kwargs)
	
	def create_payment(self, currency, gateway):
		from django.contrib.contenttypes.models import ContentType
		
		price = self.plan.prices.get(currency = currency)
		if self.period == 1:
			amount = float(price.monthly)
		else:
			amount = float(price.yearly)
		
		if self.discount:
			offer_amount = round(amount - (amount / 100.0 * self.discount.percent), 2)
			offer_months = self.discount.months
		else:
			offer_amount = 0
			offer_months = 0
		
		tax_rate = TaxRate.objects.get(
			chargeable_percent = getattr(settings, 'PAYMENTS_DEFAULT_TAXRATE')
		)
		
		if amount > 0:
			return Payment.objects.create(
				content_type = ContentType.objects.get_for_model(self),
				object_id = self.pk,
				customer = self.user,
				currency = currency,
				gateway = gateway,
				net_amount = amount,
				tax_amount = tax_rate.calculate_amount(amount),
				offer_net_amount = offer_amount,
				offer_tax_amount = tax_rate.calculate_amount(offer_amount),
				offer_months = offer_months,
				offer_description = self.discount and self.discount.name or '',
				recurring = self.period,
				trial_months = self.plan.trial_months,
				tax_rate = tax_rate
			)
		else:
			return None
	
	class Meta:
		ordering = ('-renewed', '-started')

class EmailValidation(models.Model):
	user = models.ForeignKey(User, related_name = 'email_validations', unique = True)
	guid = models.CharField(max_length = 36, unique = True)
	sent = models.DateTimeField(auto_now_add = True)
	
	def __unicode__(self):
		return self.guid
	
	def save(self, *args, **kwargs):
		if not self.guid:
			self.guid = unicode(uuid4())
		
		new = not self.pk
		super(EmailValidation, self).save(*args, **kwargs)
		
		self.user.is_active = False
		self.user.save()
		
		if new:
			render_to_mail(
				subject = u'Please confirm your email address',
				template = 'saas/mail/validate.txt',
				context = {
					'name': self.user.first_name or self.user.username,
					'guid': self.guid
				},
				recipient = self.user
			)
	
	class Meta:
		ordering = ('-sent',)
		get_latest_by = 'sent'

class PasswordReset(models.Model):
	user = models.ForeignKey(User, related_name = 'password_resets', unique = True)
	guid = models.CharField(max_length = 36, unique = True)
	sent = models.DateTimeField(auto_now_add = True)
	
	def __unicode__(self):
		return self.guid
	
	def save(self, *args, **kwargs):
		if not self.guid:
			self.guid = unicode(uuid4())
		
		new = not self.pk
		super(PasswordReset, self).save(*args, **kwargs)
		
		if new:
			render_to_mail(
				subject = u'Forgotten your password?',
				template = 'saas/mail/password-reset.txt',
				context = {
					'name': self.user.first_name or self.user.username,
					'guid': self.guid
				},
				recipient = self.user
			)
	
	def reset(self):
		password = User.objects.make_random_password(10)
		
		self.user.set_password(password)
		self.user.save()
		self.delete()
		
		render_to_mail(
			subject = u'Your new password',
			template = 'saas/mail/password.txt',
			context = {
				'name': self.user.first_name or self.user.username,
				'username': self.user.username,
				'password': password
			},
			recipient = self.user
		)
	
	class Meta:
		ordering = ('-sent',)
		get_latest_by = 'sent'
		
@receiver(payment_complete, sender = UserPlan)
def saas_payment_complete(sender, payment, **kwargs):
	logger = logging.getLogger()
	logger.info('Payment for %s complete' % payment.content_object.plan)
	
	payment.content_object.paid = True
	payment.content_object.save()

@receiver(payment_cancelled, sender = UserPlan)
def saas_payment_cancelled(sender, payment, **kwargs):
	logger = logging.getLogger()
	logger.info('Payment for %s cencelled' % payment.content_object.plan)
	
	payment.content_object.user.delete()

@receiver(payment_error, sender = UserPlan)
def saas_payment_error(sender, payment, **kwargs):
	logger = logging.getLogger()
	logger.info('Payment for %s encountered an error' % payment.content_object.plan)
	
	# payment.content_object.user.delete()

@receiver(payment_terminated, sender = UserPlan)
def saas_payment_terminated(sender, payment, **kwargs):
	logger = logging.getLogger()
	logger.info('Payment for %s terminated' % payment.content_object.plan)
	
	payment.content_object.user.delete()