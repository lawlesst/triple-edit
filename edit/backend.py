import os
import logging

from rdflib import plugin, Graph, ConjunctiveGraph, Literal, URIRef, Namespace, RDF, RDFS
from rdflib.store import Store
from rdflib.namespace import NamespaceManager, ClosedNamespace
from rdflib.query import ResultException

import uuid

#setup namespaces
#code inspired by / borrowed from https://github.com/libris/librislod
VIVO = Namespace('http://vivoweb.org/ontology/core#')
#local data namespace
D = Namespace('http://vivo.brown.edu/individual/')
BLOCAL = Namespace('http://demo.school.edu/ontology/')

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
        return g

    def get_subtract_graph(self, triple):
        """
        This is assuming that a functional property is being edited.
        """
        if triple == {}:
            return Graph()
        #We will leave the object blank.
        q = """
        CONSTRUCT {{
            <{0}> {1} ?object
        }}
        WHERE {{
            <{0}> {1} ?object
        }}
        """.format(triple['subject'], triple['predicate'])
        try:
            results = self.graph.query(q)
            subtract_graph = results.graph
        except ResultException:
            return Graph()
        return subtract_graph

    def add_remove(self, *args):
        raise NotImplementedError("Add and remove not defined.")


class Vivo15Backend(BaseBackend):
    def __init__(self, endpoint):
        #super(Vivo15Backend).__init__(self, endpoint)
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
        VIVO_URL = os.environ['VIVO_URL']
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
            VIVO_URL + 'edit/primitiveRdfEdit',
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