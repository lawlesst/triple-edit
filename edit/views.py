
from django.http import HttpResponse, HttpResponseServerError
from django.views.generic import TemplateView, View

import json

from rdflib import Graph, RDFS, URIRef, Literal

from utils import JSONResponseMixin, get_env
from services import FASTService, VIVOService

#Setup a triple store
# from backend import SQLiteBackend
# tstore =SQLiteBackend()
from backend import VivoBackend
ep = get_env('ENDPOINT')
tstore = VivoBackend(ep)

from backend import D, VIVO, RDF
from display import university, person

class ResourceView(View):

    def post(self, *args, **kwargs):
        posted = self.request.POST
        edit = json.loads(posted.get('edit'))
        if edit.get('type') == 'ck':
            add_stmts = edit['add']
            add_g = tstore.make_edit_graph(add_stmts)
            subtract_g = tstore.get_subtract_graph(add_stmts)
        elif edit.get('type') in [u'multi-tag']:
            add_stmts = edit.get('add')
            if (add_stmts is not None) and (add_stmts != {}):
                add_g = Graph()
                if add_stmts['object'] == u'new':
                    uri, g = tstore.create_resource(
                        add_stmts['range'],
                        add_stmts['text']
                    )
                    add_g += g
                    add_stmts['object'] = uri
                else:
                    #Make sure we have the text for the added KW
                    obj_uri = URIRef(add_stmts['object'])
                    add_g.add((obj_uri, RDFS.label, Literal(add_stmts['text'])))
                    #Add type.
                    atype = tstore.get_prop_from_abbrv(add_stmts['range'])
                    add_g.add((obj_uri, RDF.type, atype))

                add_g += tstore.make_edit_graph(add_stmts)
            else:
                add_g = Graph()
            remove_stmts = edit.get('subtract')
            if remove_stmts is not None:
                subtract_g = tstore.make_edit_graph(remove_stmts)
            else:
                subtract_g = Graph()
        else:
            return HttpResponseServerError("Edit failed.  Edit type not recognized.")

        done = tstore.add_remove(add_g, subtract_g)
        if done is True:
            return HttpResponse('', 200 )
        else:
            return HttpResponseServerError("Edit failed.")

        return HttpResponseServerError("Edit failed.")

class BasePropertyView(View):

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
        for row in tstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.ra.toPython()
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out


class UniversityView(TemplateView, ResourceView, BasePropertyView):
    template_name = 'university.html'

    def get_context_data(self, local_name=None, **kwargs):
        context = {}
        uri = D[local_name]
        context['uri'] = uri
        context['name'] = tstore.graph.value(subject=uri, predicate=RDFS.label)
        profile = {
            'overview': tstore.graph.value(subject=uri, predicate=VIVO.overview),
        }
        prepared_sections = []
        for section in university:
            if section['id'] == 'researchArea':
                section['data'] = json.dumps(self.get_research_areas(uri))
            elif section['id'] == 'placeResearchArea':
                section['data'] = json.dumps(self.get_place_research_areas(uri))
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
        context['sections']  = prepared_sections
        context['profile'] = profile
        return context

class IndexView(TemplateView, ResourceView):
    template_name = 'index.html'

    def get_organizations(self):
        rq = """
        select ?org ?label
        where {
            ?org a foaf:Organization .
            ?org rdfs:label ?label .
        }
        ORDER BY ?label
        LIMIT 10
        """
        out = []
        for row in tstore.graph.query(rq):
            d = {}
            d['uri'] = row.org.toPython().split('/')[-1]
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out

    def get_faculty(self):
        rq = """
        select ?fac ?label
        where {
            ?fac a vivo:FacultyMember .
            ?fac rdfs:label ?label .
        }
        ORDER BY ?label
        LIMIT 10
        """
        out = []
        for row in tstore.graph.query(rq):
            d = {}
            d['uri'] = row.fac.toPython().split('/')[-1]
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        url = self.request.resolver_match.url_name
        if url == u'index':
            context['name'] = 'Index'
            orgs = self.get_organizations()
            faculty = self.get_faculty()
            context['orgs']  = orgs
            context['people'] = faculty
        elif url == u'people':
            context['name'] = 'People'
            faculty = self.get_faculty()
            context['people'] = faculty
        elif url == u'organizations':
            context['name'] = 'Organizations'
            orgs = self.get_organizations()
            context['orgs'] = orgs
        return context

class PersonView(TemplateView, ResourceView, BasePropertyView):
    template_name = 'person.html'

    def get_research_areas(self, uri):
        rq = """
        select ?ra ?label
        where {
            ?uri vivo:hasResearchArea ?ra .
            ?ra rdfs:label ?label .
            FILTER NOT EXISTS {?ra a schema:Place }
        }
        """
        out = []
        for row in tstore.graph.query(rq, initBindings={'uri': uri}):
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
        for row in tstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.org.toPython()
            d['id'] = d['uri']
            d['text'] = row.label.toPython()
            out.append(d)
        return out

    def get_collaborators(self, uri):
        rq = """
        select ?collab ?name
        where {
            ?uri vivo:hasCollaborator ?collab .
            ?collab rdfs:label ?name .
        }"""
        out = []
        for row in tstore.graph.query(rq, initBindings={'uri': uri}):
            d = {}
            d['uri'] = row.collab.toPython()
            d['id'] = d['uri']
            d['text'] = row.name.toPython()
            out.append(d)
        return out

    def get_details(self, uri):
        #Get the name, title and other non-editable details.
        rq = """
        CONSTRUCT {
            ?fac d:name ?label .
            ?fac d:title ?title .
            ?org d:org ?orgName .
            ?collab d:collabName ?collabName .
        }
        where {
            ?fac rdfs:label ?label
            OPTIONAL {
                #Property paths are real slow.
                ?fac obo:ARG_2000028 ?vc .
                ?vc vcard:hasTitle ?t .
                ?t vcard:title ?title .
            }
            OPTIONAL {
                ?position a vivo:Position ;
                          vivo:relates ?fac ;
                          vivo:relates ?org .
                ?org a foaf:Organization.
                ?org rdfs:label ?orgName .
            }
        }
        """
        data = tstore.graph.query(rq, initBindings={'fac': uri})
        g = data.graph
        return {
            'name': g.value(subject=uri, predicate=D['name']),
            'title': g.value(subject=uri, predicate=D['title']),
            'orgs': [{'id' : o.org.toPython().replace(D, ''), 'name': o.name} for o in g.query('select ?org ?name where { ?org d:org ?name}')],
        }

    def get_context_data(self, local_name=None, **kwargs):
        context = super(PersonView, self).get_context_data(**kwargs)
        uri = D[local_name]
        details = self.get_details(uri)
        context['uri'] = uri
        context['local_name'] = uri
        #In production, this will need to be refactored because each call
        #to graph generates a SPARQL query.
        profile = {
            'overview': tstore.graph.value(subject=uri, predicate=VIVO.overview),
            'researchOverview': tstore.graph.value(subject=uri, predicate=VIVO.researchOverview),
            'teachingOverview': tstore.graph.value(subject=uri, predicate=VIVO.teachingOverview),
        }
        profile.update(details)
        prepared_sections = []
        for section in person:
            if section['id'] == 'researchArea':
                section['data'] = json.dumps(self.get_research_areas(uri))
            elif section['id'] == 'placeResearchArea':
                section['data'] = json.dumps(self.get_place_research_areas(uri))
            elif section['id'] == 'affiliations':
                section['data'] = json.dumps(self.get_affiliations(uri))
            elif section['id'] == 'collaborators':
                section['data'] = json.dumps(self.get_collaborators(uri))
            else:
                section['data'] = profile.get(section['id'])
            prepared_sections.append(section)
        context['sections']  = prepared_sections
        context['profile'] = profile
        return context


#
# - Services for autcomplete widgets
#

class JSONServiceView(View, JSONResponseMixin):
    def render_to_response(self, context):
        return JSONResponseMixin.render_to_response(self, context)

class FASTTopicAutocompleteView(JSONServiceView):

    def get(self, request, *args, **kwargs):
        fs = FASTService()
        #topics
        index = 'suggest50'
        context = {}
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)

class FASTPlaceAutocompleteView(JSONServiceView):
    def get(self, request, *args, **kwargs):
        fs = FASTService()
        #locations/geograph
        index = 'suggest51'
        context = {}
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)

class FASTOrganizationAutocompleteView(JSONServiceView):
    def get(self, request, *args, **kwargs):
        fs = FASTService()
        context = {}
        #organizations
        index = 'suggest10'
        query = self.request.GET.get('query')
        out = fs.get(query, index)
        context['results'] = out
        return self.render_to_response(context)


class VIVOCollaboratorsAutocompleteView(JSONServiceView):
    def get(self, request, *args, **kwargs):
        #fellow faculty members.
        context = {}
        vs = VIVOService()
        query = self.request.GET.get('query')
        out = vs.get(query, VIVO['FacultyMember'].toPython())
        context['results'] = out
        return self.render_to_response(context)