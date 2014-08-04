import os
import logging

from rdflib import plugin, Graph, ConjunctiveGraph, Literal, URIRef, Namespace
from rdflib import RDF, RDFS, OWL
from rdflib.store import Store
from rdflib.namespace import NamespaceManager, ClosedNamespace
from rdflib.query import ResultException
from SPARQLWrapper import SPARQLWrapper

import uuid

from utils import get_env

#setup namespaces
#code inspired by / borrowed from https://github.com/libris/librislod
VIVO = Namespace('http://vivoweb.org/ontology/core#')
SCHEMA = Namespace('http://schema.org/')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
OBO = Namespace('http://purl.obolibrary.org/obo/')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')

#local data namespace
d = get_env('NAMESPACE')
D = Namespace(d)

namespaces = {}
for k, o in vars().items():
    if isinstance(o, (Namespace, ClosedNamespace)):
        namespaces[k] = o

ns_mgr = NamespaceManager(Graph())
for k, v in namespaces.items():
    ns_mgr.bind(k.lower(), v)

rq_prefixes = u"\n".join("prefix %s: <%s>" % (k.lower(), v)
                         for k, v in namespaces.items())

prefixes = u"\n    ".join("%s: %s" % (k.lower(), v)
                          for k, v in namespaces.items()
                          if k not in u'RDF RDFS OWL XSD')
#namespace setup complete

class BaseBackend(object):
    """
    Common methods for all backends.
    """

    def make_uuid_uri(self, prefix='n'):
        return D[str(uuid.uuid4())]

    def get_prop_from_abbrv(self, prefix_prop):
        prefix, prop = prefix_prop.split(':')
        ns = namespaces.get(prefix.upper())
        if ns is None:
            raise Exception("Unknown namespace prefix: {}.".format(prefix))
        return ns[prop]

    def create_resource(self, vtype, text, uri=None):
        if uri is None:
            uri = self.make_uuid_uri()
        vclass = self.get_prop_from_abbrv(vtype)
        g = Graph()
        g.add((uri, RDFS.label, Literal(text)))
        g.add((uri, RDF.type, vclass))
        return (uri, g)

    def make_edit_graph(self, triple):
        g = Graph()
        if triple == {}:
            return g
        prefix, prop = triple['predicate'].split(':')
        ns = namespaces.get(prefix.upper())
        if ns is None:
            raise Exception("Unknown namespace prefix: {}.".format(prefix))
        pred = URIRef(ns[prop])
        obj = triple.get('object')
        subj = URIRef(triple['subject'])
        # #make_new_uri
        # if obj == u'new':
        #     uid = make_uuid()
        #     subj = URIRef(D[uid])
        is_uri = False
        try:
            is_uri = unicode(obj).startswith('http')
        except Exception, e:
            logging.warning(u"Encoding error editing object.")
            logging.warning(e)
        if is_uri is True:
            obj = URIRef(obj)
        else:
            obj = Literal(obj)
        g.add((
            subj,
            pred,
            obj,
        ))
        #Add inverse statements.
        iv = self.graph.value(subject=pred, predicate=OWL.inverseOf)
        if iv is not None:
            g.add((obj, iv, subj))
        return g

    def get_subtract_graph(self, triple):
        """
        This is assuming that a functional property is being edited.
        """
        if triple == {}:
            return Graph()
        pred = self.get_prop_from_abbrv(triple['predicate'])
        sub = URIRef(triple['subject'])
        val = self.graph.value(subject=sub, predicate=pred)
        if val is None:
            return Graph()
        else:
            subtract = Graph()
            subtract.add((sub, pred, val))
            return subtract

    def add_remove(self, *args):
        raise NotImplementedError("Add and remove not defined.")


class VivoBackend(BaseBackend):

    def __init__(self, endpoint):
        graph = ConjunctiveGraph('SPARQLStore')
        graph.open(endpoint)
        graph.namespace_manager=ns_mgr
        self.graph = graph
        self.default_graph = 'http://vitro.mannlib.cornell.edu/default/vitro-kb-2'

    def do_update(self, query):
        logging.debug(query)
        update_url = get_env('VIVO_URL') + '/api/sparqlUpdate'
        sparql = SPARQLWrapper(update_url)
        sparql.addParameter('email', get_env('VIVO_USER'))
        sparql.addParameter('password', get_env('VIVO_PASSWORD'))
        sparql.method = 'POST'
        sparql.setQuery(query)
        results = sparql.query()
        return results

    def build_clause(self, change_graph, name=None, delete=False):
        nameg = name or self.default_graph
        stmts = u''
        for subject, predicate, obj in change_graph:
            triple = "%s %s %s .\n" % (subject.n3(), predicate.n3(), obj.n3())
            stmts += triple
        if delete is False:
            return u"INSERT DATA { GRAPH <%s> { %s } }; \n" % (nameg, stmts)
        else:
            return u"DELETE DATA { GRAPH <%s> { %s } }; \n" % (nameg, stmts)

    def add_remove(self, add_g, subtract_g, name=None):
        #DELETE { GRAPH <g1> { a b c } } INSERT { GRAPH <g1> { x y z } }
        #http://www.w3.org/TR/sparql11-update/#deleteInsert
        #return self.primitive_edit(add_g, subtract_g)
        rq = u''
        add_size = len(add_g)
        remove_size = len(subtract_g)
        if (add_size == 0) and (remove_size == 0):
            logging.info("Graphs empty.  No edit made.")
        if add_size != 0:
            rq += self.build_clause(add_g, name=name)
        if remove_size != 0:
            rq += u' ' + self.build_clause(subtract_g, name=name, delete=True)
        logging.debug("SPARQL Update Query:\n".format(rq))
        self.do_update(rq)
        return True


class Vivo15Backend(BaseBackend):
    def __init__(self, endpoint):
        graph = ConjunctiveGraph('SPARQLStore')
        graph.open(endpoint)
        graph.namespace_manager=ns_mgr
        self.graph = graph

    def get_session(self):
        """
        Verify that user is logged in by issuing
        a HEAD request.  This adds overheard to
        each edit but should be minimal as it just
        verifies the session and does not follow
        redirects.
        """
        from vivo_utils import web_client
        #create a vivo_session object
        vivo_session = web_client.Session()
        ping = vivo_session.session.head(vivo_session.url + 'siteAdmin')
        if ping.status_code == 302:
            logging.debug("Creating VIVO session")
            vivo_session.login()
        else:
            logging.debug("VIVO session exists")
        return vivo_session

    def primitive_edit(self, add_graph, subtract_graph):
        """
        A update access layer via sending HTTP requests
        to VIVO web application.  This should be served
        by SPARQL update when that is available via
        a VIVO web service.
        """
        vivo_url = get_env('VIVO_URL')
        vs = self.get_session()
        if (len(add_graph) == 0) and (len(subtract_graph) == 0):
            logging.info('Add and subtract graph are both empty.  Not submitting edit.')
            return True
        #Don't post when change graphs are equal.
        if add_graph == subtract_graph:
            logging.info('Add and subtract graph are equal.  Not submitting edit.')
            return True
        payload = dict(
            additions=add_graph.serialize(format='n3'),
            retractions=subtract_graph.serialize(format='n3'),
        )
        resp = vs.session.post(
            vivo_url + '/edit/primitiveRdfEdit',
            data=payload,
            verify=False
        )
        if resp.status_code != 200:
            logging.error("VIVO app response:\n" + resp.text)
            logging.error("Add graph:\n" + add_graph.serialize(format='nt'))
            logging.error("Subtract graph:\n" + subtract_graph.serialize(format='nt'))
            raise VIVOEditError('VIVO data editing failed')
        return True

    def add_remove(self, add_g, subtract_g):
        return self.primitive_edit(add_g, subtract_g)

class VIVOEditError(Exception):
    def __init__self(self, message, Errors):
        #http://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python
        Exception.__init__(self, message)
        self.Errors = Errors


class SQLiteBackend(BaseBackend):
    def __init__(self):
        from django.conf import settings
        store = plugin.get("SQLAlchemy", Store)(identifier='demo')
        graph = Graph(store, identifier='demo')
        graph.namespace_manager = ns_mgr
        graph.open(Literal("sqlite:///" + settings.BASE_DIR + "demo.db"), create=True)
        self.graph = graph

    def add_remove(self, add_g, remove_g):
        for trip in remove_g:
            self.graph.remove(trip)
        for trip in add_g:
            self.graph.add(trip)
        self.graph.commit()
        return True