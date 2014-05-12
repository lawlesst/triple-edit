
from django.http import HttpResponse, HttpResponseServerError
from django.views.generic import TemplateView, View

import json
import urllib

import requests

from utils import JSONResponseMixin, get_env

# from backend import SQLiteBackend
# vstore =SQLiteBackend()

from backend import Vivo15Backend
ep = get_env('ENDPOINT')
vstore = Vivo15Backend(ep)

class ResourceView(View):

    def post(self, *args, **kwargs):
        #from backend import vstore, make_edit_graph, get_subtract_graph, add_remove, VIVO
        from rdflib import Graph, RDFS, URIRef, Literal
        posted = self.request.POST
        #import pdb; pdb.set_trace()
        edit = json.loads(posted.get('edit'))
        if edit.get('type') == 'ck':
            #import ipdb; ipdb.set_trace();
            add_stmts = edit['add']
            add_g = vstore.make_edit_graph(add_stmts)
            subtract_g = vstore.get_subtract_graph(add_stmts)
        elif edit.get('type') in [u'multi-tag']:
            add_stmts = edit.get('add')
            if (add_stmts is not None) and (add_stmts != {}):
                add_g = Graph()
                if add_stmts['object'] == u'new':
                    uri, g = vstore.create_resource(
                        add_stmts['range'],
                        add_stmts['text']
                    )
                    add_g += g
                    add_stmts['object'] = uri
                else:
                    #Make sure we have the text for the added KW
                    obj_uri = URIRef(add_stmts['object'])
                    add_g.add((obj_uri, RDFS.label, Literal(add_stmts['text'])))
                add_g += vstore.make_edit_graph(add_stmts)
            else:
                add_g = Graph()
            remove_stmts = edit.get('subtract')
            if remove_stmts is not None:
                subtract_g = vstore.make_edit_graph(remove_stmts)
            else:
                subtract_g = Graph()
        else:
            return HttpResponseServerError("Edit failed.  Edit type not recognized.")

        done = vstore.add_remove(add_g, subtract_g)
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

    def get_research_areas(self, uri):
        rq = """
        select ?ra ?label
        where {
            ?uri vivo:hasResearchArea ?ra .
            ?ra rdfs:label ?label .
        }
        """
        out = []
        for row in vstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.ra.toPython()
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out

    def get_geo_research_areas(self, uri):
        rq = """
        select ?ra ?label
        where {
            ?uri blocal:hasGeographicResearchArea ?ra .
            ?ra rdfs:label ?label .
        }
        """
        out = []
        for row in vstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.ra.toPython()
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out

    def get_context_data(self, local_name=None, **kwargs):
        from backend import D, VIVO, RDFS
        from display import person
        context = super(PersonView, self).get_context_data(**kwargs)
        uri = D[local_name]
        context['uri'] = uri
        context['name'] = vstore.graph.value(subject=uri, predicate=RDFS.label)
        context['sections'] = person
        #This will come from a sparql query.
        profile = {
            'title': vstore.graph.value(subject=uri, predicate=VIVO.preferredTitle),
            'overview': vstore.graph.value(subject=uri, predicate=VIVO.overview),
            'researchOverview': vstore.graph.value(subject=uri, predicate=VIVO.researchOverview),
            'teachingOverview': vstore.graph.value(subject=uri, predicate=VIVO.teachingOverview)
        }
        prepared_sections = []
        for section in person:
            if section['id'] == 'researchArea':
                section['data'] = json.dumps(self.get_research_areas(uri))
            elif section['id'] == 'geoResearchArea':
                section['data'] = json.dumps(self.get_geo_research_areas(uri))
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
            #get the v
        context['sections']  = prepared_sections
        context['profile'] = profile
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
        #import ipdb; ipdb.set_trace()
        api_base_url = 'http://fast.oclc.org/searchfast/fastsuggest'
        context = {}
        query = self.request.GET.get('query')
        #FAST topics are suggest50 - see http://experimental.worldcat.org/fast/assignfast/
        url = api_base_url + '?query=' + urllib.quote(query) + '&queryIndex=suggest50&queryReturn=idroot%2Cauth%2Ctype&suggest=autoSubject'
        response = requests.get(url)
        results = response.json()
        #import ipdb; ipdb.set_trace()
        out = []
        for position, item in enumerate(results['response']['docs']):
            if item.get('type') != u'auth':
                continue
            name = item.get('auth')
            pid = item.get('idroot')
            d = {}
            d['uri'] = self.make_uri(pid)
            d['id'] = pid
            d['text'] = name
            out.append(d)
        context['results'] = out
        return self.render_to_response(context)

class FASTGeoAutocompleteView(FASTTopicAutocompleteView):
    def get(self, request, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
        api_base_url = 'http://fast.oclc.org/searchfast/fastsuggest'
        context = {}
        query = self.request.GET.get('query')
        #FAST topics are suggest50 - see http://experimental.worldcat.org/fast/assignfast/
        url = api_base_url + '?query=' + urllib.quote(query) + '&queryIndex=suggest51&queryReturn=idroot%2Cauth%2Ctype&suggest=autoSubject'
        response = requests.get(url)
        results = response.json()
        #import ipdb; ipdb.set_trace()
        out = []
        for position, item in enumerate(results['response']['docs']):
            if item.get('type') != u'auth':
                continue
            name = item.get('auth')
            pid = item.get('idroot')
            d = {}
            d['uri'] = self.make_uri(pid)
            d['id'] = pid
            d['text'] = name
            out.append(d)
        context['results'] = out
        return self.render_to_response(context)