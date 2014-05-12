import urllib

import requests

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