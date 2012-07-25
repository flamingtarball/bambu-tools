#!/usr/bin/env python
# encoding: utf-8

from django import forms

class OAuthTokenInput(forms.HiddenInput):
	def __init__(self, provider_field, **kwargs):
		self.provider_field = provider_field
		super(OAuthTokenInput, self).__init__(**kwargs)
	
	def render(self, name, value, attrs = None):
		from django.utils.safestring import mark_safe
		from django.core.urlresolvers import reverse
		
		final_attrs = self.build_attrs(attrs, type = self.input_type, name = name)
		html = super(OAuthTokenInput, self).render(name, value, attrs)
		html += '<a id="%(id)s_link" class="button" ' \
		'target="_blank" style="display: none;"></a>' % {
			'domain': 'blah.com',
			'id': final_attrs['id']
		}
		
		js = """
		(function($) {
		    $(document).ready(
				function() {
					$('#""" + final_attrs['id'] + """').each(
						function() {
							var q = ':[name=\"""" + self.provider_field + """\"]';\
							var field = $('#""" + final_attrs['id'] + """');
							var link = $('#""" + final_attrs['id'] + """_link');
							var select = $(this).closest('form').find(q);
							
							link.bind('click',
								function(e) {
									e.preventDefault();
									
									if(!$(this).attr('href')) {
										return;
									}
									
									window.open(
										$(this).attr('href') + '&input_id=""" + final_attrs['id'] + """',
										'megaphone-oauth', 'width=980,height=640'
									);
								}
							);
							
							select.bind('change',
								function() {
									if(!$(this).val()) {
										link.hide();
										return;
									}
									
									var text = $(this).find('option:selected').html();
									var url = '""" + reverse('megaphone_auth') + """?provider=' + $(this).val();
									link.html('Connect to ' + text).attr('href', url).removeAttr('disabled').show();
									field.val('');
								}
							);
							
							if(select.val()) {
								var text = select.find('option:selected').html();
								var url = '""" + reverse('megaphone_auth') + """?provider=' + $(this).val();
								link.html('Connected to ' + text).attr('disabled', 'disabled').show();
							} else {
								link.attr('disabled', 'disabled').text('Choose a provider').show();
							}
						}
					);
				}
			)
		})(django.jQuery);
		"""
		
		return mark_safe(html + '<script>' + js + '</script>')