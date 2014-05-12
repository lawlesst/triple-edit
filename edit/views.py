from django.conf import settings

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.generic import TemplateView, View

import json

from utils import JSONResponseMixin

class ResourceView(View):

    def post(self, *args, **kwargs):
        from backend import vstore, make_edit_graph, get_subtract_graph, add_remove
        from rdflib import Graph
        posted = self.request.POST
        #import pdb; pdb.set_trace()
        edit = json.loads(posted.get('edit'))
        if edit.get('type') == 'ck':
            add_stmts = edit['add']
            add_g = make_edit_graph(add_stmts)
            subtract_g = get_subtract_graph(add_stmts)
        elif edit.get('type') in [u'multi-tag']:
            add_stmts = edit.get('add')
            if add_stmts is not None:
                add_g = make_edit_graph(add_stmts)
            else:
                add_g = Graph()
            remove_stmts = edit.get('subtract')
            if remove_stmts is not None:
                subtract_g = make_edit_graph(remove_stmts)
            else:
                subtract_g = Graph()
        else:
            return HttpResponseServerError("Edit failed.  Edit type not recognized.")

        done = add_remove(add_g, subtract_g)
        if done is True:
            return HttpResponse('', 200 )
        else:
            return HttpResponseServerError("Edit failed.")

        #return HttpResponse('', 200 )
        return HttpResponseServerError("Edit failed.")


class UniversityView(TemplateView, ResourceView):
    template_name = 'university.html'

    def get_context_data(self, local_name=None, **kwargs):
        context = super(UniversityView, self).get_context_data(**kwargs)
        context['hello'] = "Here"
        return context

class PersonView(TemplateView, ResourceView):
    template_name = 'person.html'

    def get_context_data(self, local_name=None, **kwargs):
        from backend import D, VIVO, vstore
        from display import person
        context = super(PersonView, self).get_context_data(**kwargs)
        uri = D[local_name]
        context['uri'] = uri
        context['name'] = "Smith, James"
        context['overview'] = "A short bio"
        context['sections'] = person
        #This will come from a sparql query.
        profile = {
            'overview': vstore.value(subject=uri, predicate=VIVO.overview),
            'research-overview': vstore.value(subject=uri, predicate=VIVO.researchOverview)
        }
        prepared_sections = []
        for section in person:
            print section['id'], section['predicate']
            if section['id'] == 'research-area':
                section['data'] = ['crime', 'history', 'BBC']
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
            #get the v
        context['sections']  = prepared_sections
        return context

class FASTTopicAutocompleteView(View, JSONResponseMixin):
    def render_to_response(self, context):
        return JSONResponseMixin.render_to_response(self, context)

    def make_uri(self, fast_id):
        fast_uri_base = 'http://id.worldcat.org/fast/{0}'
        fid = fast_id.lstrip('fst').lstrip('0')
        fast_uri = fast_uri_base.format(fid)
        return fast_uri

    def get(self, request, *args, **kwargs):
        import requests
        import urllib
        #import ipdb; ipdb.set_trace()
        api_base_url = 'http://fast.oclc.org/searchfast/fastsuggest'
        #http://localhost:8080/vivo/autocomplete?tokenize=true&term=crime&type=http%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23Concept&multipleTypes=null
        context = {}
        query = self.request.GET.get('query')
        url = api_base_url + '?query=' + urllib.quote(query) + '&rows=30&queryReturn=suggestall%2Cidroot%2Cauth%2cscore&suggest=autoSubject&queryIndex=suggest10&wt=json'
        response = requests.get(url)
        results = response.json()
        #import ipdb; ipdb.set_trace()
        out = []
        for position, item in enumerate(results['response']['docs']):
            name = item.get('auth')
            pid = item.get('idroot')
            d = {}
            d['uri'] = self.make_uri(pid)
            d['id'] = pid
            d['text'] = name
            out.append(d)
        context['results'] = out
        return self.render_to_response(context)

