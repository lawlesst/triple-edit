from django.conf.urls import patterns, url

from views import (
    ResourceView,
    PersonView,
    UniversityView,
    FASTTopicAutocompleteView,
    FASTGeoAutocompleteView
)


urlpatterns = patterns('',
    url(r'^person/(?P<local_name>[a-z0-9]+)/$', PersonView.as_view(), name='person'),
    url(r'^org/display/(?P<local_name>[a-z0-9]+)/$', UniversityView.as_view(), name='university'),
    url(r'^index/$', IndexView.as_view(), name='index'),
    url(r'^edit/', ResourceView.as_view(), name='edit'),
    url(r'^service/fast/topic/$', FASTTopicAutocompleteView.as_view(), name='fast-topic'),
    url(r'^service/fast/geo/$', FASTGeoAutocompleteView.as_view(), name='fast-geo'),
)
