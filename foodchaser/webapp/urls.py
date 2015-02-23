from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webapp.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^foodchaser/', include('foodchaser.urls')),
    url(r'^selectable/', include('selectable.urls')),
    url(r'', include('social_auth.urls')),
    url(r'^$', 'foodchaser.views.homepage'),
    (r'^static/(?P<path>.*)$',
    'django.views.static.serve', 
    {'document_root': settings.STATIC_ROOT}),
)

##if settings.DEBUG:
##    import debug_toolbar
##    urlpatterns += patterns('',
##        url(r'^__debug__/', include(debug_toolbar.urls)),
##    )
