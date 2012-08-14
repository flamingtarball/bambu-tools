from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils.timezone import utc
from taggit.models import Tag
from datetime import datetime
from bambu.blog.models import Post, Category
from bambu.blog.helpers import view_filter, title_parts
from bambu.comments.forms import CommentForm

def _context(request):
	return {
		'categories': Category.objects.filter(posts__isnull = False).distinct(),
		'dates': Post.objects.live().dates('date', 'month'),
		'menu_selection': 'blog'
	}

def posts(request, **kwargs):
	posts = Post.objects.live()
	templates = ['blog/posts.html']
	context = _context(request)
	breadcrumb_trail = []
	
	if 'year' in kwargs:
		if 'month' in kwargs:
			if 'day' in kwargs:
				date = datetime(
					int(kwargs['year']),
					int(kwargs['month']),
					int(kwargs['day'])
				).replace(tzinfo = utc)
				
				context['day'] = date.strftime('%B %d, %Y')
				
				breadcrumb_trail = (
					('../../../', u'Blog'),
					('../../', date.strftime('%Y')),
					('../', date.strftime('%B')),
					('', date.strftime('%d'))
				)
				
				templates.insert(0, 'blog/posts-day.html')
			else:
				date = datetime(
					int(kwargs['year']),
					int(kwargs['month']),
					1
				).replace(tzinfo = utc)
				
				context['month'] = date.strftime('%B %Y')
				
				breadcrumb_trail = (
					('../../', u'Blog'),
					('../', date.strftime('%Y')),
					('', date.strftime('%B'))
				)
				
				templates.insert(0, 'blog/posts-month.html')
		else:
			context['year'] = kwargs['year']
			templates.insert(0, 'blog/posts-year.html')
			
			breadcrumb_trail = (
				('../', u'Blog'),
				('', int(kwargs['year'])),
			)
	else:
		breadcrumb_trail = (
			('', u'Blog'),
		)
	
	if 'category' in kwargs:
		category = get_object_or_404(Category, slug = kwargs['category'])
		context['category'] = category
		templates.insert(0, 'blog/posts-category.html')
		breadcrumb_trail = (
			('../', u'Blog'),
			('', category.name)
		)
	elif 'tag' in kwargs:
		tag = get_object_or_404(Tag, slug = kwargs['tag'])
		context['tag'] = tag
		templates.insert(0, 'blog/posts-tag.html')
		breadcrumb_trail = (
			('../', u'Blog'),
			('', tag.name)
		)
	elif 'username' in kwargs:
		author = get_object_or_404(User, username = kwargs['username'])
		context['author'] = author
		templates.insert(0, 'blog/posts-author.html')
		breadcrumb_trail = (
			('../', u'Blog'),
			('', author.get_full_name() or author.username)
		)
	
	context['posts'] = view_filter(**kwargs)
	context['breadcrumb_trail'] = breadcrumb_trail
	context['title_parts'] = title_parts(**kwargs)
	
	return TemplateResponse(
		request,
		templates,
		context
	)

def post(request, year, month, day, slug):
	try:
		post = Post.objects.live().get(
			date__year = int(year),
			date__month = int(month),
			date__day = int(day),
			slug = slug
		)
	except Post.DoesNotExist:
		raise Http404('Post not found.')
	
	context = _context(request)
	context['post'] = post
	context['day'] = post.date.strftime('%B %d, %Y')
	context['breadcrumb_trail'] = (
		('../../../../', u'Blog'),
		('../../../', post.date.strftime('%Y')),
		('../../', post.date.strftime('%B')),
		('../', post.date.strftime('%d')),
		('', post.title)
	)
	
	context['title_parts'] = (post.title, u'Blog')
	
	if not request.GET.get('comment-sent'):
		initial = {}
	
		if request.user.is_authenticated():
			initial = {
				'name': request.user.get_full_name() or request.user.username,
				'email': request.user.email,
				'website': 'http://%s/' % Site.objects.get_current().domain
			}
	
		context['comment_form'] = CommentForm(initial = initial)
	
	return TemplateResponse(
		request,
		'blog/post.html',
		context
	)

@require_POST
def post_comment(request, year, month, day, slug):
	try:
		post = Post.objects.live().get(
			date__year = int(year),
			date__month = int(month),
			date__day = int(day),
			slug = slug
		)
	except Post.DoesNotExist:
		raise Http404('Post not found.')
	
	form = CommentForm(request.POST)
	if request.POST.get('h0n3ytr4p'):
		return HttpResponse('')
	
	if form.is_valid():
		comment = form.save(commit = False)
		
		if request.POST.get('content_type'):
			comment.content_type = ContentType.objects.get(
				pk = int(request.POST['content_type'])
			)
		else:
			comment.content_type = ContentType.objects.get_for_model(post)
		
		if request.POST.get('object_id'):
			comment.object_id = ContentType.objects.get(
				pk = int(request.POST['object_id'])
			).pk
		else:
			comment.object_id = post.pk
		
		comment.save()
		
		messages.add_message(
			request,
			messages.SUCCESS,
			u'Your comment has been submitted successfully.'
		)
		
		return HttpResponseRedirect(
			'%s?comment-sent=true' % post.get_absolute_url()
		)
	
	context = _context(request)
	context['post'] = post
	context['day'] = post.date.strftime('%B %d, %Y')
	context['breadcrumb_trail'] = (
		('../../../../../', u'Blog'),
		('../../../../', post.date.strftime('%Y')),
		('../../../', post.date.strftime('%B')),
		('../../', post.date.strftime('%d')),
		('../', post.title),
		('', u'Post comment')
	)
	
	context['title_parts'] = (post.title, u'Blog')
	context['comment_form'] = form
	context['comment_form_action'] = '.'
	
	return TemplateResponse(
		request,
		'blog/post.html',
		context
	)