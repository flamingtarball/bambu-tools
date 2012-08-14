from django.conf.urls.defaults import patterns, include, url
from bambu.bootstrap.decorators import body_classes
from bambu.blog.views import posts, post
from bambu.blog.feeds import BlogFeed

urlpatterns = patterns('bambu.blog.views',
	url(r'^$', body_classes(posts, 'blog'), name = 'blog_posts'),
	url(r'^feed/$', BlogFeed(), name = 'blog_posts_feed'),
	url(r'^(?P<year>\d{4})/$', body_classes(posts, 'blog', 'blog-year'), name = 'blog_posts_by_year'),
	url(r'^(?P<year>\d{4})/feed/$', BlogFeed(), name = 'blog_posts_by_year_feed'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/$', body_classes(posts, 'blog', 'blog-month'), name = 'blog_posts_by_month'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/feed/$', BlogFeed, name = 'blog_posts_by_month_feed'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', body_classes(posts, 'blog', 'blog-day'), name = 'blog_posts_by_day'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/feed/$', BlogFeed(), name = 'blog_posts_by_day_feed'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[\w-]+)/$', body_classes(post, 'blog', 'blog-post'), name = 'blog_post'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[\w-]+)/comment/$', 'post_comment', name = 'blog_post_comment'),
	url(r'^tag/(?P<tag>[\w-]+)/$', body_classes(posts, 'blog'), name = 'blog_posts_by_tag'),
	url(r'^tag/(?P<tag>[\w-]+)/feed/$', BlogFeed(), name = 'blog_posts_by_tag_feed'),
	url(r'^category/(?P<category>[\w-]+)/$', body_classes(posts, 'blog'), name = 'blog_posts_by_category'),
	url(r'^category/(?P<category>[\w-]+)/feed/$', BlogFeed(), name = 'blog_posts_by_category_feed'),
	url(r'^author/(?P<username>[\w]+)/$', body_classes(posts, 'blog'), name = 'blog_posts_by_author'),
	url(r'^author/(?P<username>[\w]+)/feed/$', BlogFeed(), name = 'blog_posts_by_author_feed')
)