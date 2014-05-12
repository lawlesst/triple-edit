from django.conf import settings
from django.conf.urls import patterns, include, url

import edit

urlpatterns = patterns('',
    url(r'', include('edit.urls', namespace='edit')),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
    )
