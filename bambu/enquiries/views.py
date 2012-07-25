from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from bambu.enquiries.models import Enquiry
from bambu.enquiries.forms import EnquiryForm

def enquiry(request):
	form = EnquiryForm(request.POST or None)
	
	if form.is_valid():
		form.save()
		return HttpResponseRedirect('thanks/')
	
	return TemplateResponse(
		request,
		'enquiries/enquiry.html',
		{
			'form': form,
			'menu_selection': 'enquiry'
		}
	)
	
def enquiry_thanks(request):
	return TemplateResponse(
		request,
		'enquiries/thanks.html',
	)