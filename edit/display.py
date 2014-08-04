person = [
   {
      'id':'overview',
      'predicate':'vivo:overview',
      'etype':'ckedit',
      'label':'Overview'
   },
   {
      'id':'collaborators',
      'predicate':'vivo:hasCollaborator',
      #multi-tag-select means the value has to exist.
      'etype':'multi-tag-select',
      'label':'Collaborators',
      'range': 'vivo:FacultyMember',
   },
   # {
   #    'id':'researchOverview',
   #    'predicate':'vivo:researchOverview',
   #    'etype':'ckedit',
   #    'label':'Research overview'
   # },
   {
    'id': 'researchArea',
    'predicate': 'vivo:hasResearchArea',
    'etype': 'multi-tag',
    'range': 'skos:Concept',
    'label': 'Research areas',
   },
   # {
   #    'id':'teachingOverview',
   #    'predicate':'vivo:teachingOverview',
   #    'etype':'ckedit',
   #    'label':'Teaching overview'
   # },
   {
    'id': 'placeResearchArea',
    'predicate': 'vivo:hasResearchArea',
    'etype': 'multi-tag',
    'range': 'schema:Place',
    'label': 'Geographic research areas',
   },
   {
    'id': 'affiliations',
    'predicate': 'schema:affiliation',
    'etype': 'multi-tag',
    'range': 'schema:Organization',
    'label': 'Affiliated organizations',
   }
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