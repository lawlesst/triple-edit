
from django.http import HttpResponse, HttpResponseServerError
from django.views.generic import TemplateView, View

import json

from utils import JSONResponseMixin, get_env
from services import FASTService

# from backend import SQLiteBackend
# vstore =SQLiteBackend()

#A VIVO 15 Backend.
from backend import Vivo15Backend
#from backend import Vivo16Backend
ep = get_env('ENDPOINT')
vstore = Vivo16Backend(ep)

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
        from backend import D, VIVO, RDFS
        from display import university
        context = {}
        uri = D[local_name]
        context['uri'] = uri
        context['name'] = vstore.graph.value(subject=uri, predicate=RDFS.label)
        profile = {
            'overview': vstore.graph.value(subject=uri, predicate=VIVO.overview),
        }
        prepared_sections = []
        for section in university:
            if section['id'] == 'researchArea':
                section['data'] = json.dumps(self.get_research_areas(uri))
            elif section['id'] == 'geoResearchArea':
                section['data'] = json.dumps(self.get_geo_research_areas(uri))
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
        context['sections']  = prepared_sections
        context['profile'] = profile
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

    def get_place_research_areas(self, uri):
        rq = """
        select ?ra ?label
        where {
            ?uri vivo:hasResearchArea ?ra .
            ?ra a schema:Place .
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

    def get_affiliations(self, uri):
        rq = """
        select ?org ?label
        where {
            ?uri schema:affiliation ?org .
            ?org rdfs:label ?label .
        }
        """
        out = []
        for row in vstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.org.toPython()
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
        #In production, this will neeed to be refactored because each call
        #to graph generates a SPARQL query.
        profile = {
            'title': vstore.graph.value(subject=uri, predicate=VIVO.preferredTitle),
            'overview': vstore.graph.value(subject=uri, predicate=VIVO.overview),
            'researchOverview': vstore.graph.value(subject=uri, predicate=VIVO.researchOverview),
            'teachingOverview': vstore.graph.value(subject=uri, predicate=VIVO.teachingOverview),
        }
        prepared_sections = []
        for section in person:
            if section['id'] == 'researchArea':
                section['data'] = json.dumps(self.get_research_areas(uri))
            elif section['id'] == 'placeResearchArea':
                section['data'] = json.dumps(self.get_place_research_areas(uri))
            elif section['id'] == 'affiliations':
                section['data'] = json.dumps(self.get_affiliations(uri))
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
        context['sections']  = prepared_sections
        context['profile'] = profile
        return context


#
# - Services for autcomplete widgets
#

class FASTServiceView(View, JSONResponseMixin):
    def render_to_response(self, context):
        return JSONResponseMixin.render_to_response(self, context)

class FASTTopicAutocompleteView(FASTServiceView):

    def get(self, request, *args, **kwargs):
        fs = FASTService()
        #topics
        index = 'suggest50'
        context = {}
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)

class FASTPlaceAutocompleteView(FASTServiceView):
    def get(self, request, *args, **kwargs):
        fs = FASTService()
        #locations/geograph
        index = 'suggest51'
        context = {}
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)

class FASTOrganizationAutocompleteView(FASTServiceView):
    def get(self, request, *args, **kwargs):
        fs = FASTService()
        #organizations
        index = 'suggest10'
        context = {}
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)