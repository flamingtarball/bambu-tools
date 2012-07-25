from django import forms
from bambu.enquiries.models import Enquiry

class EnquiryForm(forms.ModelForm):
	class Meta:
		model = Enquiry