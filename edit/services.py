import urllib

import requests

from utils import get_env

class FASTService(object):

    def __init__(self):
        pass

    def make_uri(self, fast_id):
        fast_uri_base = 'http://id.worldcat.org/fast/{0}'
        fid = fast_id.lstrip('fst').lstrip('0')
        fast_uri = fast_uri_base.format(fid)
        return fast_uri

    def get(self, query, index):
        #import ipdb; ipdb.set_trace()
        api_base_url = 'http://fast.oclc.org/searchfast/fastsuggest'
        #FAST topics are suggest50 - see http://experimental.worldcat.org/fast/assignfast/
        url = api_base_url + '?query=' + urllib.quote(query) + \
            '&queryIndex={}'.format(index) + \
            '&queryReturn=idroot%2Cauth%2Ctype' + \
            '%2c{}'.format(index) + \
            '&suggest=autoSubject'
        response = requests.get(url)
        results = response.json()
        out = []
        for position, item in enumerate(results['response']['docs']):
            rec_type = item.get('type')
            name = item.get('auth')
            #For alternate terms whow the alternate label instead.
            #ToDo: use Select2 display function to display and format
            #the authorized form of the term.
            if rec_type != u'auth':
                try:
                    name = u'{}'.format(item.get(index)[0])
                except IndexError:
                    continue
            pid = item.get('idroot')
            d = {}
            d['uri'] = self.make_uri(pid)
            d['id'] = pid
            d['text'] = name
            out.append(d)
        return out


class VIVOService(object):
    def __init__(self):
        from mysolr import Solr
        surl = get_env('SOLR_URL')
        self.solr = Solr(surl)

    def get(self, query, class_type):
        out = []
        #Will use acNameStemmed for now.  Can construct a more intelligent query
        #later if necessary.
        query = {
            'q': u'acNameStemmed:{0} type:{1}'.format(query, class_type),
            'fl': 'URI,nameRaw,PREFERRED_TITLE',
            'rows': 20
        }
        response = self.solr.search(**query)
        #Massage the Solr response.
        for doc in response.documents:
            d = {}
            d['uri'] = doc['URI']
            d['id'] = doc['URI']
            d['text'] = "{} - {}".format(
                doc['nameRaw'][0],
                doc['PREFERRED_TITLE'][0]
            )
            out.append(d)
        return out
