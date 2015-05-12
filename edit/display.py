from vdm.models import VResource
from backend import HUB, VIVO
#TMP = Namespace('http://localhost/tmp/')

class NameAuthority(VResource):
    """
    People
    """
    def init_query(self):
        return """
        CONSTRUCT {
            ?subject a schema:Person ;
                rdfs:label ?label ;
                hub:wikidata ?wikidata ;
                hub:viaf ?viaf ;
                vivo:overview ?overview .
        }
        WHERE {
            {
              ?subject a schema:Person ;
                rdfs:label ?label .
            OPTIONAL {?subject hub:wikidata ?wikidata }
            OPTIONAL {?subject hub:viaf ?viaf }
            OPTIONAL {?subject vivo:overview ?overview .}
            }
        }
        """

    def researchers(self):
        return self.get_related(VIVO.researchAreaOf)

    def as_dict(self):
        return dict(
            uri=self.identifier.toPython(),
            label=self.get_label(),
            wikidata=self.get_first_literal(HUB.wikidata),
            viaf=self.get_first_literal(HUB.viaf),
            overview=self.get_first_literal(VIVO.overview)
        )




person = [
   {
      'id':'overview',
      'predicate':'vivo:overview',
      'etype':'ckedit',
      'label':'Overview'
   },
   # {
   #    'id':'collaborators',
   #    'predicate':'vivo:hasCollaborator',
   #    #multi-tag-select means the value has to exist.
   #    'etype':'multi-tag-select',
   #    'label':'Collaborators',
   #    'range': 'vivo:FacultyMember',
   # },
   # {
   #    'id':'researchOverview',
   #    'predicate':'vivo:researchOverview',
   #    'etype':'ckedit',
   #    'label':'Research overview'
   # },
   # {
   #  'id': 'researchArea',
   #  'predicate': 'vivo:hasResearchArea',
   #  'etype': 'multi-tag',
   #  'range': 'skos:Concept',
   #  'label': 'Research areas',
   # },
   # {
   #    'id':'teachingOverview',
   #    'predicate':'vivo:teachingOverview',
   #    'etype':'ckedit',
   #    'label':'Teaching overview'
   # },
   # {
   #  'id': 'placeResearchArea',
   #  'predicate': 'vivo:hasResearchArea',
   #  'etype': 'multi-tag',
   #  'range': 'schema:Place',
   #  'label': 'Geographic research areas',
   # },
   # {
   #  'id': 'affiliations',
   #  'predicate': 'schema:affiliation',
   #  'etype': 'multi-tag',
   #  'range': 'schema:Organization',
   #  'label': 'Affiliated organizations',
   # }
]

organization =[
   {
      'id':'overview',
      'predicate':'vivo:overview',
      'etype':'ckedit',
      'label':'Overview'
   },
   {
    'id': 'placeResearchArea',
    'predicate': 'vivo:hasResearchArea',
    'etype': 'multi-tag',
    'range': 'schema:Place',
    'label': 'Geographic research areas',
   },
]