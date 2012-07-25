from django import forms
from bambu.blog.models import Post
from django.utils.timezone import utc
from datetime import datetime

class PostForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(PostForm, self).__init__(*args, **kwargs)
		self.fields['date'].initial = datetime.utcnow().replace(tzinfo = utc)
		self.fields['tags'].required = False
	
	class Meta:
		model = Post