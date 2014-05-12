from django.conf import settings

import logging

from rdflib import plugin, Graph, Literal, URIRef, Namespace, RDF
from rdflib.store import Store
from rdflib.namespace import NamespaceManager, ClosedNamespace
from rdflib.query import ResultException

#setup namespaces
#code inspired by / borrowed from https://github.com/libris/librislod
VIVO = Namespace('http://vivoweb.org/ontology/core#')
#local data namespace
D = Namespace('http://demo.school.edu/individual/')

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


store = plugin.get("SQLAlchemy", Store)(identifier='demo')
graph = Graph(store, identifier='demo')
graph.namespace_manager = ns_mgr
graph.open(Literal("sqlite:///" + settings.BASE_DIR + "demo.db"), create=True)
graph.add((D['jsmith'], RDF.type, VIVO.FacultyMember))

vstore = graph

def make_uuid(prefix='n'):
    import uuid
    return str(uuid.uuid4())

def make_edit_graph(triple):
    g = Graph()
    prefix, prop = triple['predicate'].split(':')
    ns = namespaces.get(prefix.upper())
    if ns is None:
        raise Exception("Unknown namespace prefix: {}.".format(prefix))
    pred = URIRef(ns[prop])
    obj = triple.get('object')
    subj = URIRef(triple['subject'])
    #make_new_uri
    if subj == u'new':
        uid = make_uuid()
        subj = URIRef(D[uid])
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

def get_subtract_graph(triple):
    """
    This is assuming that a functional property is being edited.
    """
    #We will leave the object blank.
    q = """
    CONSTRUCT {{
        <{0}> {1} ?object
    }}
    WHERE {{
        <{0}> {1} ?object
    }}
    """.format(triple['subject'], triple['predicate'])
    results = vstore.query(q)
    if results is not None:
        subtract_graph = results.graph
    else:
        subtract_graph = Graph()
    return subtract_graph

def add_remove(add_g, remove_g):
    for trip in remove_g:
        graph.remove(trip)
    for trip in add_g:
        graph.add(trip)
    graph.commit()
    return True