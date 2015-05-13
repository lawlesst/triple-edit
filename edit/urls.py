from django.conf.urls import patterns, url

from views import (
    ResourceView,
    PersonView,
    OrganizationView,
    IndexView,
    FASTTopicAutocompleteView,
    FASTPlaceAutocompleteView,
    FASTOrganizationAutocompleteView,
    VIVOCollaboratorsAutocompleteView,
    PersonSearchView

)


urlpatterns = patterns('',
    url(r'^people/$', IndexView.as_view(), name='people'),
    url(r'^organizations/$', IndexView.as_view(), name='organizations'),
    url(r'^person/(?P<local_name>[a-z0-9]+)/$', PersonView.as_view(), name='person'),
    url(r'^org/(?P<local_name>[a-z0-9]+)/$', OrganizationView.as_view(), name='organization'),
    url(r'^edit/', ResourceView.as_view(), name='edit'),
    url(r'^service/fast/topic/$', FASTTopicAutocompleteView.as_view(), name='fast-topic'),
    url(r'^service/fast/place/$', FASTPlaceAutocompleteView.as_view(), name='fast-place'),
    url(r'^service/fast/org/$', FASTOrganizationAutocompleteView.as_view(), name='fast-org'),
    url(r'^service/vivo/collaborators/$', VIVOCollaboratorsAutocompleteView.as_view(), name='vivo-collaborators'),
    url(r'^service/person/search/$', PersonSearchView.as_view(), name='people-search'),
    #everything else
    url(r'^$', IndexView.as_view(), name='index')
)
